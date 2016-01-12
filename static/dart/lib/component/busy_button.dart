import 'dart:html';
import 'dart:js';

import 'package:angular/angular.dart';

/// A button that can display a busy state (disabled + spinner).
@Component(
    selector: 'busy-button',
    templateUrl: 'packages/hgprofiler/component/busy_button.html',
    useShadowDom: false
)
class BusyButtonComponent {
    @NgAttr('type')
    String type = 'default';

    @NgAttr('size')
    String size;

    @NgOneWay('click')
    Function click;

    @NgOneWay('data')
    dynamic data;

    bool busy = false;

    Element _element;

    BusyButtonComponent(this._element) {
        this._element.onClick.listen((event) {
            this.busy = true;
            click(event, data, this.reset);
        });
    }

    void reset() {
        this.busy = false;
    }
}
