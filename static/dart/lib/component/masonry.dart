import 'dart:async';
import 'dart:html';

import 'package:angular/angular.dart';
import 'package:collection/equality.dart';

/// A component that provides a masonry layout.
@Component(
    selector: 'masonry',
    template: '<content></content>',
    useShadowDom: false
)
class MasonryComponent implements ScopeAware, ShadowRootAware {
    @NgOneWay('column-width')
    int columnWidth;

    @NgOneWay('column-gap')
    int columnGap;

    @NgOneWay('margin-bottom')
    int marginBottom;

    num _columnCount;
    num _columnWidth;
    Element _element;
    List<int> _lastLayout;
    num _parentWidth = -1;
    num _tileCount;

    /// Listen for scope events.
    void set scope(Scope scope) {
        scope.on('masonry.layout').listen((ScopeEvent e) {
            this.setChildrenWidths();
        });
    }

    MasonryComponent(this._element);

    /// Runs after shadow root element connected.
    void onShadowRoot(HtmlElement shadowRoot) {
        // Perform an initial layout.
        new Future(() {
            if (this.marginBottom == null) {
                this.marginBottom = this.columnGap;
            }

            this.setChildrenWidths();
            this._parentWidth = this._element.getBoundingClientRect().width;
        });

        // Redo layout when the parent element width changes.
        window.onResize.listen((Event e) {
            num parentWidth = this._element.getBoundingClientRect().width;

            if ((parentWidth - this._parentWidth).abs() > 0.1) {
                this.setChildrenWidths();
                this._parentWidth = parentWidth;
            }
        });
    }

    /// Arrange children into columns.
    ///
    /// This is the second phase of rendering. At this point, children should
    /// already be correctly sized. Because the browser may take a while to
    /// resize child elements, this step runs repeatedly until it produces the
    /// same layout twice, indicating that the DOM has settled.
    void positionChildren() {
        List<int> columnHeights = new List<int>.filled(this._columnCount, 0);

        // Position elements.
        for (HtmlElement child in this._element.children) {
            if (child is ScriptElement) {
                continue;
            }

            // Find the shortest column
            int shortestColumn = 0;

            for (int i=1; i<this._columnCount; i++) {
                if (columnHeights[i] < columnHeights[shortestColumn]) {
                    shortestColumn = i;
                }
            }

            // Resize this child and put it in this column.
            num left = shortestColumn * (this._columnWidth + this.columnGap);
            num top = columnHeights[shortestColumn];

            child.style.position = 'absolute';
            child.style.left = '${left}px';
            child.style.top = '${top}px';
            child.style.display = 'block';

            columnHeights[shortestColumn] += child.getBoundingClientRect().height + this.marginBottom;
        }

        // Check if the layout has settled.
        if (this._lastLayout == null ||
            !const ListEquality().equals(this._lastLayout, columnHeights)) {

            this._lastLayout = columnHeights;
            new Timer(new Duration(milliseconds:100), this.positionChildren);
        }
    }

    /// Compute and set desired width of child elements.
    ///
    /// This is phase 1 of the rendering process. We do this first and then
    /// wait a bit for the browser to re-flow each child box. (Otherwise the
    /// height of the child box may change after we have already positioned it.)
    void setChildrenWidths([Event e]) {
        num parentWidth = this._element.getBoundingClientRect().width;

        if (parentWidth == 0) {
            // Still waiting for DOM to settle. Try again later.
            new Timer(new Duration(milliseconds: 100), this.setChildrenWidths);
            return;
        }

        num unitWidth = this.columnWidth + this.columnGap;
        this._columnCount = (parentWidth / unitWidth).round();
        num columnPixels = parentWidth - (this.columnGap * (this._columnCount - 1));
        this._columnWidth = columnPixels / this._columnCount;
        this._tileCount = 0;

        for (HtmlElement child in this._element.children) {
            if (child is ScriptElement) {
                continue;
            }

            this._tileCount++;
            child.style.width = '${this._columnWidth}px';
        }

        if (this._tileCount == 0) {
            // Still waiting for DOM to settle. Try again later.
            new Timer(new Duration(milliseconds: 100), this.setChildrenWidths);
            return;
        }

        new Timer(new Duration(milliseconds: 100), this.positionChildren);
    }
}
