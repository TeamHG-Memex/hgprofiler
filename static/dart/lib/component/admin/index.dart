import 'dart:async';
import 'dart:html';

import 'package:angular/angular.dart';
import 'package:hgprofiler/authentication.dart';
import 'package:hgprofiler/component/breadcrumbs.dart';
import 'package:hgprofiler/component/title.dart';
import 'package:hgprofiler/rest_api.dart';

/// A component for viewing and modifying credentials.
@Component(
    selector: 'admin-index',
    templateUrl: 'packages/hgprofiler/component/admin/index.html',
    useShadowDom: false
)
class AdminIndexComponent {
    List<Breadcrumb> crumbs = [
        new Breadcrumb('HGProfiler', '/'),
        new Breadcrumb('Administration'),
    ];

    final TitleService _ts;

    /// Constructor.
    AdminIndexComponent(this._ts) {
        this._ts.title = 'Profiles';
    }
}
