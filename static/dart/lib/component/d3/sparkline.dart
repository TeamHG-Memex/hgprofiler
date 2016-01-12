import 'dart:async';
import 'dart:html';
import 'dart:js';
import 'dart:math';

import 'package:angular/angular.dart';
import 'package:bootjack/bootjack.dart';

/// A small D3 widget for rendering a sparkline.
@Component(
    selector: 'sparkline',
    template: '<svg width="10" height="10"></svg>',
    useShadowDom: false
)
class SparklineComponent implements ShadowRootAware {
    final Element _element;

    /// An array of numbers that represents series data for the chart.
    @NgOneWay('series')
    List<num> series;

    /// An array of strings that represents labels for element of ``series``.
    @NgOneWay('labels')
    List<String> labels;

    /// Singular name of unit, e.g. "inch" or "record".
    @NgAttr('unit')
    String unitSingular;

    /// Plural name of unit, e.g. "inches" or "records". If not specified, then
    /// the default is unitSingular + 's'.
    @NgAttr('unit-plural')
    String unitPlural;

    /// A CSS color declaration that will be used for the line.
    @NgAttr('color')
    String color = 'black';

    /// Width of the element in pixels.
    @NgAttr('width')
    num width;

    /// Width of the element in pixels.
    @NgAttr('height')
    num height;

    /// The minimum Y value (helpful for keeping a consistent scale
    /// across multiple sparklines).
    @NgAttr('ymin')
    num yMin;

    /// The maximum Y value (helpful for keeping a consistent scale
    /// across multiple sparklines).
    @NgAttr('ymax')
    num yMax;

    String tooltipText;

    SparklineComponent(this._element);

    /// This is called by ShadowRootAware when the Shadow DOM has been set up.
    ///
    /// We delay one event loop with Future() so that any nested Shadow DOMs
    /// can also be set up before we render.
    void onShadowRoot(HtmlElement shadowRoot) {
        new Future(() {
            // Set up unit text.
            if (this.unitSingular == null) {
                this.unitSingular = '';
                this.unitPlural = '';
            } else if (this.unitPlural == null) {
                this.unitPlural = this.unitSingular + 's';
            }

            // Initialize element.
            var svgElement = this._element.querySelector('svg');
            var tooltip = new Tooltip(
                svgElement,
                trigger: 'manual',
                animation: false,
                title: (el) => this.tooltipText
            );

            var d3 = context['d3'];

            // Set up X axis.
            var jsXDomain = new JsObject.jsify([0, series.length]);
            var jsXRange = new JsObject.jsify([0, width]);

            var x = d3['scale']
                .callMethod('linear')
                .callMethod('domain', [jsXDomain])
                .callMethod('range', [jsXRange]);

            // Set up Y axis.
            if (this.yMin == null) {
                this.yMin = 0;
            }

            if (this.yMax == null) {
                this.yMax = series.reduce(max);
            }

            var jsYDomain = new JsObject.jsify([this.yMin, this.yMax]);
            var jsYRange = new JsObject.jsify([height, 0]);

            var y = d3['scale']
                .callMethod('linear')
                .callMethod('domain', [jsYDomain])
                .callMethod('range', [jsYRange]);

            // Render graph.
            var graph = d3
                .callMethod('select', [svgElement])
                .callMethod('attr', ['width', width])
                .callMethod('attr', ['height', height]);

            var line = d3['svg']
                .callMethod('line')
                .callMethod('x', [(d,i) => x.apply([i])])
                .callMethod('y', [(d,i) => y.apply([d])]);

            var jsSvgPath = line.apply([new JsObject.jsify(series)]);

            graph.callMethod('append', ['svg:path'])
                 .callMethod('attr', ['fill', 'none'])
                 .callMethod('attr', ['stroke', color])
                 .callMethod('attr', ['d', jsSvgPath]);

            // Add a mouseover effect.
            var highlight = d3
                .callMethod('select', [svgElement])
                .callMethod('append', ['line'])
                .callMethod('attr', ['y1', 0])
                .callMethod('attr', ['y2', this.height])
                .callMethod('style', ['display', 'none'])
                .callMethod('style', ['stroke', 'rgba(51, 122, 183, 0.75)'])
                .callMethod('style', ['stroke-width', '3px'])
                .callMethod('style', ['z-index', -1]);

            var showHighlight = (el, datum, index) {
                highlight.callMethod('style', ['display', null]);
            };

            var moveHighlight = (el, datum, index) {
                // Draw a highlight.
                var location = d3.callMethod('mouse', [svgElement]);
                var inverted = x.callMethod('invert', [location[0]]);
                var index = d3.callMethod('round', [inverted]);

                if (index < 0) {
                    index = 0;
                } else if (index >= series.length) {
                    index = series.length - 1;
                }

                var xCoord = x.apply([index]);
                highlight.callMethod('attr', ['x1', xCoord])
                         .callMethod('attr', ['x2', xCoord]);

                // Display a tooltip.
                tooltip.hide();
                this.tooltipText = '';
                num value = this.series[index];

                if (this.labels != null && this.labels.length > index) {
                    this.tooltipText += '${this.labels[index]}: ';
                }

                this.tooltipText += value.toString();

                if (value == 1 && this.unitSingular != null) {
                    this.tooltipText += ' ${this.unitSingular}';
                } else if (value != 1 && this.unitPlural != null) {
                    this.tooltipText += ' ${this.unitPlural}';
                }

                tooltip.show();
            };

            var hideHighlight = (el, datum, index) {
                highlight.callMethod('style', ['display', 'none']);
                tooltip.hide();
            };

            var mouseRect = d3
                .callMethod('select', [svgElement])
                .callMethod('append', ['rect'])
                .callMethod('attr', ['width', '${this.width}px'])
                .callMethod('attr', ['height', '${this.height}px'])
                .callMethod('style', ['fill', 'none'])
                .callMethod('style', ['pointer-events', 'all'])
                .callMethod('on', ['mouseover', showHighlight])
                .callMethod('on', ['mousemove', moveHighlight])
                .callMethod('on', ['mouseout', hideHighlight]);
        });
    }
}
