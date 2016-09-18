import 'dart:html';

import 'package:angular/angular.dart';

/// A service for holding the current page title.
@Injectable()
class TitleService {
    String _title;

    String get title => this._title;

    void set title(String t) {
        window.document.title = '$t — Profiler';
    }

    TitleService() {
        this.title = 'Loading…';
    }
}
