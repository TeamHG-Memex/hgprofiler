import 'dart:js';
import 'dart:html';

import 'package:angular/angular.dart';

/// A component that presents a modal dialog.
@Component(
    selector: 'modal',
    templateUrl: 'packages/hgprofiler/component/modal.html',
    useShadowDom: false
)
class ModalComponent {
    String body;
    String icon = 'fa-warning';
    String title;
    String type = 'default';
    bool visible = false;

    ModalComponent() {
        document.addEventListener('modal', this.displayModal);
    }

    void displayModal(Event e) {
        if (e.detail['body'] == null) {
            throw Exception('Modal event requires a body.');
        } else {
            this.body = e.detail['body'];
        }

        if (e.detail['title'] == null) {
            throw Exception('Modal event requires a title.');
        } else {
            this.title = e.detail['title'];
        }

        if (e.detail['icon'] != null) {
            this.icon = e.detail['icon'];
        }

        if (e.detail['type'] != null) {
            this.type = e.detail['type'];
        }

        this.visible = true;
    }
}
