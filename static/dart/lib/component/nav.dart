import 'dart:html';

import 'package:angular/angular.dart';

import 'package:hgprofiler/authentication.dart';

/// The top navigation bar.
@Component(
    selector: 'nav',
    templateUrl: 'packages/hgprofiler/component/nav.html',
    useShadowDom: false
)
class NavComponent {
    AuthenticationController auth;
    bool showDevFeatures = false;

    String _secretWord = 'DEVMODE';
    int _index = 0;

    /// Constructor.
    NavComponent(this.auth) {
        if (window.localStorage['devmode'] != null) {
            showDevFeatures = window.localStorage['devmode'] == 'true';
        } else {
            window.localStorage['devmode'] = this.showDevFeatures ? 'true' : 'false';
        }

        // Show development features when user types "DEVMODE".
        document.body.onKeyPress.listen((e) {
            String typedLetter;

            try {
                typedLetter = new String.fromCharCodes([e.charCode]);
            } catch (RangeError) {
                this._index = 0;
                return;
            }

            if (this._secretWord[this._index] == typedLetter) {
                this._index++;

                if (this._index == _secretWord.length) {
                    this.showDevFeatures = !this.showDevFeatures;
                    window.localStorage['devmode'] = this.showDevFeatures ? 'true' : 'false';
                    this._index = 0;
                }
            } else {
                this._index = 0;
            }
        });
    }
}
