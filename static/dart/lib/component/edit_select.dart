import 'dart:async';
import 'dart:html';

import 'package:angular/angular.dart';

/// A component for making some text editable with a dropdown.
@Component(
    selector: 'edit-select',
    templateUrl: 'packages/hgprofiler/component/edit_select.html',
    useShadowDom: false
)
class EditSelectComponent implements ShadowRootAware {
    @NgOneWay('onsave')
    Function onSave;

    @NgOneWay('options')
    List options;

    @NgOneWay('selected-index')
    int selectedIndex;

    bool editing = false;

    final Element _element;
    HTMLElement _select;

    /// Constructor.
    EditSelectComponent(this._element);

    /// Get references to child elements.
    void onShadowRoot(HtmlElement shadowRoot) {
        document.addEventListener('start-edit', this.handleEditEvent);

        new Future(() {
            // Can't selectedIndex until ng-repeat finishes.
            this._select = this._element.querySelector('select');
            this._select.selectedIndex = this.selectedIndex;
        });
    }

    /// Revert element text.
    void cancelEdit() {
        this.finishEdit();
        this._select.selectedIndex = this.selectedIndex;
    }

    /// Disable editing mode.
    void finishEdit() {
        this.editing = false;
    }

    /// Handle a 'start-edit' event.
    void handleEditEvent(Event e) {
        if (e.detail != this) {
            // The event was fired by some other element, which means
            // we should cancel this element.
            this.cancelEdit();
        }
    }

    /// Update element text and call save event handler.
    void saveEdit() {
        this.finishEdit();

        if (this._select.selectedIndex != this.selectedIndex &&
            this.onSave != null) {

            this.onSave(this._select.selectedIndex);
        }
    }

    /// Switch the component into editing mode.
    void startEdit() {
        this.editing = true;
        document.dispatchEvent(new CustomEvent('start-edit', detail: this));

        new Future(() {
            // focus() doesn't work until after ng-show finishes.
            this._select.focus();
        });
    }
}
