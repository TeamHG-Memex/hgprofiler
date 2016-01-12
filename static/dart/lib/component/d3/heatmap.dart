import 'dart:async';
import 'dart:html';
import 'dart:js';
import 'dart:math';

import 'package:angular/angular.dart';
import 'package:bootjack/bootjack.dart';

/// A D3 widget for rendering a week+hour heatmap.
@Component(
    selector: 'heatmap',
    template: '<svg></svg>',
    useShadowDom: false
)
class HeatmapComponent implements ScopeAware, ShadowRootAware {
    final Element _element;

    /// An array of day/hour/value objects.
    @NgOneWay('data')
    List<Map> data;

    @NgOneWay('click')
    Function onClick;

    Completer shadowRootCompleter;
    HtmlElement svgElement;
    String tooltipText;
    List<String> times;
    Map tooltips;

    final List<String> colors = [
        '#DDDDDD', // light grey
        '#DDDD00', // mustard yellow
        '#D9A600', // light orange
        '#D56F00', // orange
        '#A82D00', // red
        '#6B0000', // dark red
    ];

    final List<String> days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

    /// Constructor.
    HeatmapComponent(this._element) {
        this.shadowRootCompleter = new Completer();
        this.tooltips = new Map();

        times = new List<String>();

        for (int i = 0; i <= 23; i++) {
            times.add(i.toString().padLeft(2,'0') + ':00');
        }
    }

    /// Handle a click event on a cell.
    void handleCellClick(datum, index, _) {
        if (datum['value'] != 0) {
            this.onClick(datum['day'], datum['hour']);
        }
    }

    /// When new data is received, it should be rendered, but we must be careful
    /// not to try rendering before the shadowRoot has been set up.
    void handleData(newValue, prevValue) {
        this.shadowRootCompleter.future.then((_) => this.render(newValue));
    }

    /// Handle a mouse out event on a cell.
    void handleCellOut(datum, index, _) {
        var targetEl = context['d3']['event'].target;

        if (this.tooltips.containsKey(targetEl)) {
            this.tooltips[targetEl].hide();
        }
    }

    /// Handle a mouse over event on a cell.
    void handleCellOver(datum, index, _) {
        var targetEl = context['d3']['event'].target;

        if (!this.tooltips.containsKey(targetEl)) {
            String hourStart = this.times[datum["hour"]];
            String hourEnd = hourStart.replaceFirst(':00', ':59', 2);
            String titleText = '${this.days[datum["day"]]} '
                               '$hourStart-$hourEnd:&nbsp;'
                               '${datum["value"]} items.';

            if (datum['value'] != 0) {
                titleText += '<br>(Click the cell to view.)';
            }

            var tooltip = new Tooltip(
                targetEl,
                trigger: 'manual',
                animation: false,
                title: (el) => titleText,
                container: window.document.body,
                html: true
            );

            this.tooltips[targetEl] = tooltip;
        }

        this.tooltips[targetEl].show();
    }

    /// This is called by ShadowRootAware when the Shadow DOM has been set up.
    ///
    /// We delay one event loop with Future() so that any nested Shadow DOMs
    /// can also be set up before we render.
    void onShadowRoot(HtmlElement shadowRoot) {
        this.shadowRootCompleter.complete(new Future(() {
            this.svgElement = this._element.querySelector('svg');
            window.onResize.listen((e) => this.render(this.data));
        }));
    }

    /// Render the heatmap with d3.
    void render(List<Map> data) {
        if (data == null){
            return;
        }

        // Set up size and spacing.
        num marginTop = 40;
        num marginLeft = 40;
        num legendPaddingTop = 10;
        num legendPaddingBottom = 20;
        num cellPadding = 2;

        num elWidth = this._element.offsetWidth;
        num mapWidth = elWidth - marginLeft;
        num gridSize = (mapWidth / 24 - cellPadding).floor();
        num elHeight = marginTop + (gridSize + cellPadding) * 8 + legendPaddingTop + legendPaddingBottom;

        num maxValue = 0;
        for (Map datum in data) {
            if (datum['value'] > maxValue) {
                maxValue = datum['value'];
            }
        }

        List<num> colorDomain;
        List<String> colorRange;

        if (maxValue >= 8) {
            colorDomain = [
                0,
                1,
                maxValue / 4,
                maxValue / 2,
                3 * maxValue / 4,
                maxValue
            ];
            colorRange = this.colors;
        } else if (maxValue >= 4) {
            colorDomain = [
                0,
                1,
                maxValue/2,
                maxValue
            ];
            colorRange = this.colors.sublist(0, 3);
        } else {
            colorDomain = [
                0,
                1,
                maxValue
            ];
            colorRange = this.colors.sublist(0, 2);
        }

        var d3 = context['d3'];

        var colorScale = d3['scale']
            .callMethod('quantile', [])
            .callMethod('domain', [new JsObject.jsify(colorDomain)])
            .callMethod('range', [new JsObject.jsify(colorRange)]);

        var svg = d3
            .callMethod('select', [this.svgElement])
            .callMethod('attr', ['width', elWidth])
            .callMethod('attr', ['height', elHeight]);

        svg.callMethod('selectAll', ['*'])
           .callMethod('remove', []);

        // Render vertical axis.
        num yAxisMarginLeft = marginLeft - 5;
        num yAxisMarginTop = marginTop + gridSize / 2;
        String yAxisTransform = 'translate($yAxisMarginLeft, $yAxisMarginTop)';

        var dayLabels = svg
            .callMethod('append', ['g'])
            .callMethod('attr', ['transform', yAxisTransform])
            .callMethod('selectAll', ['.dayLabel'])
            .callMethod('data', [new JsObject.jsify(this.days)])
            .callMethod('enter', [])
            .callMethod('append', ['text'])
            .callMethod('text', [(d, i, _) => d])
            .callMethod('attr', ['x', 0])
            .callMethod('attr', ['y', (d, i, _) => i * (gridSize + cellPadding)])
            .callMethod('style', ['text-anchor', 'end'])
            .callMethod('style', ['alignment-baseline', 'middle'])
            .callMethod('attr', ['class', 'axis']);

        num xAxisMarginLeft = marginLeft + gridSize / 2;
        num xAxisMarginTop = marginTop - 5;
        String xAxisTransform = 'translate($xAxisMarginLeft, $xAxisMarginTop)';
        Function rotate = (d, i, _) => 'rotate(-45,' + (i * (gridSize + cellPadding)).toString() + ',0)';

        // Render horizontal axis.
        var timeLabels = svg
            .callMethod('append', ['g'])
            .callMethod('attr', ['transform', xAxisTransform])
            .callMethod('selectAll', ['.timeLabel'])
            .callMethod('data', [new JsObject.jsify(this.times)])
            .callMethod('enter', [])
            .callMethod('append', ['text'])
            .callMethod('text', [(d, i, _) => d])
            .callMethod('attr', ['x', (d, i, _) => i * (gridSize + cellPadding)])
            .callMethod('attr', ['y', 0])
            .callMethod('attr', ['transform', rotate])
            .callMethod('style', ['text-anchor', 'start'])
            .callMethod('attr', ['class', 'axis']);

        // Render cells.
        var heatmap = svg
            .callMethod('append', ['g'])
            .callMethod('attr', ['transform', 'translate($marginLeft, $marginTop)'])
            .callMethod('selectAll', ['.cell'])
            .callMethod('data', [new JsObject.jsify(data)])
            .callMethod('enter', [])
            .callMethod('append', ['rect'])
            .callMethod('attr', ['x', (d, i, _) => d['hour'] * (gridSize + cellPadding)])
            .callMethod('attr', ['y', (d, i, _) => d['day'] * (gridSize + cellPadding)])
            .callMethod('attr', ['width', gridSize])
            .callMethod('attr', ['height', gridSize])
            .callMethod('attr', ['class', 'cell'])
            .callMethod('attr', ['href', 'https://google.com'])
            .callMethod('style', ['fill', this.colors[0]])
            .callMethod('on', ['mouseover', this.handleCellOver])
            .callMethod('on', ['mouseout', this.handleCellOut])
            .callMethod('on', ['click', this.handleCellClick]);

        heatmap.callMethod('transition', [])
               .callMethod('duration', [1000])
               .callMethod('style', ['fill', (d, i, _) => colorScale.apply([d['value']])]);

        // Render legend.
        var buckets = [0]..addAll(colorScale.callMethod('quantiles', []));
        num legendMarginTop = marginTop + 7 * (gridSize + cellPadding) + legendPaddingTop;
        num legendTextMargin = 3 * (gridSize + cellPadding);
        String legendTransform = 'translate($marginLeft, $legendMarginTop)';

        var legendGroup = svg
            .callMethod('append', ['g'])
            .callMethod('attr', ['transform', legendTransform]);

        legendGroup.callMethod('append', ['text'])
                   .callMethod('text', ['Legend:'])
                   .callMethod('attr', ['x', legendTextMargin - 5])
                   .callMethod('attr', ['y', gridSize + 5])
                   .callMethod('attr', ['class', 'legend'])
                   .callMethod('style', ['text-anchor', 'end'])
                   .callMethod('style', ['alignment-baseline', 'text-before-edge']);

        var legend = legendGroup
            .callMethod('selectAll', ['.legend'])
            .callMethod('data', [new JsObject.jsify(buckets), (d, i) => d])
            .callMethod('enter', [])
            .callMethod('append', ['g'])
            .callMethod('attr', ['class', 'legend']);

        Function legendRectX = (d, i, _) {
            return legendTextMargin + (gridSize + cellPadding) * i * 2;
        };

        legend.callMethod('append', ['rect'])
              .callMethod('attr', ['x', legendRectX])
              .callMethod('attr', ['y', 0])
              .callMethod('attr', ['width', gridSize * 2 + cellPadding])
              .callMethod('attr', ['height', gridSize])
              .callMethod('style', ['fill', (d, i, _) => colors[i]]);

        Function legendText = (d, i, _) {
            num cur = d.round();
            if (i == 0) {
                return '0';
            } else if (i == buckets.length - 1) {
                return '$cur-$maxValue';
            } else {
                num next = buckets[i+1].round()-1;
                if (cur == next) {
                    return cur.toString();
                } else {
                    return '$cur-$next';
                }
            }
        };

        Function legendTextX = (d, i, _) {
            return legendTextMargin +
                   (gridSize + cellPadding) * i * 2 +
                   gridSize;
        };

        legend.callMethod('append', ['text'])
              .callMethod('text', [legendText])
              .callMethod('attr', ['x', legendTextX])
              .callMethod('attr', ['y', gridSize + 5])
              .callMethod('attr', ['class', 'legend'])
              .callMethod('style', ['text-anchor', 'middle'])
              .callMethod('style', ['alignment-baseline', 'text-before-edge']);
    }

    /// Watch for changes to our data.
    void set scope(Scope scope) {
        scope.watch('data', this.handleData);
    }
}
