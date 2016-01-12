import 'dart:html';
import 'dart:js';
import 'dart:math';

import 'package:angular/angular.dart';

/// A small D3 widget that represents a surface that can be grabbed for drag
/// and drop operations.
@Component(
    selector: 'grip',
    template: '<svg></svg>',
    useShadowDom: false
)
class GripComponent implements ShadowRootAware {
    /// Reference to the <grip> element.
    final Element _element;

    /// A CSS color declaration that will be used for the boxes.
    @NgAttr('color')
    String color = 'black';

    /// Width of the element in pixels.
    @NgOneWay('rows')
    int rows = 5;

    /// Width of the element in pixels.
    @NgOneWay('cols')
    int cols = 3;

    /// Size of box in pixels.
    @NgOneWay('box-size')
    int boxSize = 2;

    /// Size of gutter (space between boxes) in pixels.
    @NgOneWay('gutter-size')
    int gutterSize = 1;

    GripComponent(this._element);

    void onShadowRoot(HtmlElement shadowRoot) {
        var svgElement = this._element.querySelector('svg');
        var d3 = context['d3'];

        int boxAndGutterSize = this.boxSize + this.gutterSize;
        int width = this.cols * (boxAndGutterSize) - this.gutterSize;
        int height = this.rows * (boxAndGutterSize) - this.gutterSize;

        var graphic = d3
            .callMethod('select', [svgElement])
            .callMethod('attr', ['width', width])
            .callMethod('attr', ['height', height]);

        for (int row in new List.generate(this.rows, (i) => i)) {
            for (int col in new List.generate(this.cols, (i) => i)) {
                graphic.callMethod('append', ['rect'])
                       .callMethod('attr', ['x', col * boxAndGutterSize])
                       .callMethod('attr', ['y', row * boxAndGutterSize])
                       .callMethod('attr', ['width', this.boxSize])
                       .callMethod('attr', ['height', this.boxSize])
                       .callMethod('attr', ['fill', this.color]);
            }
        }
    }
}
