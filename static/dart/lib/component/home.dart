import 'dart:async';
import 'dart:convert';
import 'dart:html';

import 'package:angular/angular.dart';
import 'package:hgprofiler/component/title.dart';
import 'package:hgprofiler/mixin/sort.dart';
import 'package:hgprofiler/rest_api.dart';

/// The home view.
@Component(
    selector: 'home',
    templateUrl: 'packages/hgprofiler/component/home.html',
    useShadowDom: false
)
class HomeComponent extends Object {
    RestApiController _api;
    RouteProvider _rp;
    TitleService _ts;

    /// Constructor.
    HomeComponent(this._api, this._rp, this._ts) {
        this._ts.title = 'Home';
    }
}
