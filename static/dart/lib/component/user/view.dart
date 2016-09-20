import 'dart:async';
import 'dart:html';
import 'dart:js';

import 'package:angular/angular.dart';
import 'package:hgprofiler/authentication.dart';
import 'package:hgprofiler/component/breadcrumbs.dart';
import 'package:hgprofiler/component/title.dart';
import 'package:hgprofiler/model/user.dart';
import 'package:hgprofiler/rest_api.dart';
import 'package:bootjack/bootjack.dart';
import 'package:dquery/dquery.dart';

/// A controller for viewing and editing an application user.
@Component(
    selector: 'user',
    templateUrl: 'packages/hgprofiler/component/user/view.html',
    useShadowDom: false
)
class UserComponent {
    AuthenticationController auth;
    bool canEdit = false;
    List<Breadcrumb> crumbs;
    String displayName;
    String error;
    int id;
    int loading = 0;
    String message;
    Blob thumbData;
    User user;

    final RestApiController _api;
    final RouteProvider _rp;
    final TitleService _ts;

    /// Constructor.
    UserComponent(this.auth, this._api, this._rp, this._ts) {
        String idParam = Uri.decodeComponent(this._rp.parameters['id']);
        this.id = int.parse(idParam, radix:10);
        this.canEdit = this.auth.isAdmin() || this.id == this.auth.currentUser.id;

        this.crumbs = [
            new Breadcrumb('Profiler', '/'),
            new Breadcrumb('User Directory', '/user'),
            new Breadcrumb(this.id.toString()),
        ];

        this._fetchUser();
    }

    /// Save changes to this user.
    void saveUser() {
        Map body = {
            'agency': document.getElementById('agency').value,
            'email': document.getElementById('email').value,
            'name': document.getElementById('name').value,
            'location': document.getElementById('location').value,
            'phone': document.getElementById('phone').value,
            'thumb': user.thumb,
        };

        if (this.auth.isAdmin()) {
            Element isAdmin = document.getElementById('role');

            if (isAdmin != null) {
                body['is_admin'] = isAdmin.value == 'admin';
            }
        }

        String password = document.getElementById('password').value;

        if (!password.isEmpty) {
            body['password'] = password;
        }

        this.loading++;
        this._api
            .put('/api/user/' + this.id.toString(), body, needsAuth: true)
            .then((response) {
                this.error = null;
                this.message = 'User profile updated.';
                this.user = new User.fromJson(response.data);

                if (this.user.id == this.auth.currentUser.id) {
                    this.auth.currentUser = this.user;
                }

                displayName = this.user.name != null
                            ? this.user.name
                            : this.user.email;

                this.crumbs[this.crumbs.length-1] = new Breadcrumb(displayName);
                this._ts.title = displayName;
            })
            .catchError((response) {
                this.message = null;
                this.error = response.data['message'];
            })
            .whenComplete(() {
                this.loading--;
            });
    }

    /// When a thumbnail file is selected, smoothly rescale it to 32x32 px.
    void resizeThumb(Event event) {
        File file = event.target.files.first;
        FileReader fr = new FileReader();

        if (!file.type.startsWith('image/')) {
            this.error = 'The thumbnail must be an image file.';
            return;
        }

        fr.onLoadEnd.listen((ProgressEvent pe) {
            this.thumbData = fr.result.toString();

            ImageElement img = window.document.createElement('img');
            img.src = thumbData;

            // This multiple scale approach is a quick way to get smooth
            // downsampling in Chrome. (Not sure if it works in other browsers.)
            var srcCanvas = window.document.createElement('canvas');
            srcCanvas.width = 128;
            srcCanvas.height = 128;
            srcCanvas.getContext('2d')
                ..drawImageScaled(img, 0, 0, 128, 128)
                ..drawImageScaledFromSource(srcCanvas, 0, 0, 128, 128, 0, 0, 64, 64);

            var dstCanvas = window.document.createElement('canvas');
            dstCanvas.width = 32;
            dstCanvas.height = 32;
            dstCanvas.getContext('2d')
                ..drawImageScaledFromSource(srcCanvas, 0, 0, 64, 64, 0, 0, 32, 32);

            this.user.thumb = dstCanvas.toDataUrl('image/png').split(',')[1];
        });

        fr.readAsDataUrl(file);
    }

    /// Open the file selection dialog.
    void selectFile() {
        window.document.getElementById('thumb-file').click();
    }

    /// Fetch data about this user.
    Future _fetchUser() {
        Completer completer = new Completer();
        this.loading++;

        this._api
            .get('/api/user/${this.id}', needsAuth: true)
            .then((response) {
                this.user = new User.fromJson(response.data);

                displayName = this.user.name != null
                            ? this.user.name
                            : this.user.email;

                this.crumbs[this.crumbs.length-1] = new Breadcrumb(displayName);
                this._ts.title = displayName;
            })
            .whenComplete(() {
                this.loading--;
                completer.complete();
            });

        return completer.future;
    }
}
