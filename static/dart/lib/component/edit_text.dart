import 'dart:async';
import 'dart:html';

import 'package:angular/angular.dart';

/// A component for making some text editable.
@Component(
    selector: 'edit-text',
    templateUrl: 'packages/hgprofiler/component/edit_text.html',
    useShadowDom: false
)
class EditTextComponent implements ShadowRootAware {
    @NgOneWay('onsave')
    Function onSave;

    @NgAttr('size')
    int size;

    @NgOneWay('text')
    String text;

    bool editing = false;

    final Element _element;
    HTMLElement _input;

    /// Constructor.
    EditTextComponent(this._element);

    /// Revert element text.
    void cancelEdit([Event e]) {
        this.finishEdit();
        this._input.value = this.text;
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

    /// Handle enter key.
    void handleKeyPress(KeyboardEvent event) {
        if (event.keyCode == KeyCode.ENTER) {
            this.saveEdit();
        }
    }

    /// Get references to child elements.
    void onShadowRoot(HtmlElement shadowRoot) {
        document.addEventListener('start-edit', this.handleEditEvent);
        this._input = this._element.querySelector('input');
    }

    /// Update element text and call save event handler.
    void saveEdit() {
        this.finishEdit();

        if (this._input.value != text && this.onSave != null) {
            this.onSave(this._input.value);
        }
    }

    /// Switch the component into editing mode.
    void startEdit() {
        this.editing = true;
        document.dispatchEvent(new CustomEvent('start-edit', detail: this));

        new Future(() {
            // focus() doesn't work until after ng-show finishes.
            this._input.focus();
            this._input.select();
        });
    }
}
