import 'dart:js';

import 'package:angular/angular.dart';

/// A component that converts Markdown text into HTML.
@Component(
    selector: 'markdown',
    template: '<div ng-bind-html="html"></div>',
    useShadowDom: false
)
class MarkdownComponent implements ScopeAware {
    @NgOneWay('text')
    String text;

    String html;

    /// Watch for changes to the 'text' attribute.
    void set scope(Scope scope) {
        scope.watch('text', (v, p) {
            render();
        });
    }

    /// Converts Markdown to HTML.
    void render() {
        var markdown = context['markdown'];

        if (text != null) {
            if (text.length > 3500) {
                this.html = '<p><strong><i class="fa fa-exclamation-triangle">'
                            '</i>This post is too large to be rendered. '
                            'Therefore, it is being displayed in raw form.'
                            '</strong></p>${this.text}';
            } else {
                Map parseTree = markdown.callMethod('parse', [this.text]);
                Map htmlTree = markdown.callMethod('toHTMLTree', [parseTree]);
                treeVisitor(htmlTree, null);
                this.html = markdown.callMethod('renderJsonML', [htmlTree]);
            }
        }
    }

    /// Recursively visit nodes in a JsonML HTML tree.
    ///
    /// We can do fancy things, like rewriting link hrefs and replacing images
    /// with placeholders.
    ///
    /// Take a look at the examples on the [JsonML page](http://www.jsonml.org/)
    /// to get a feel for how this tree structure is traversed.
    void treeVisitor(JsArray node, JsArray parent) {
        String type = node[0];
        JsObject attributes;
        JsArray children;

        if (node.length > 1) {
            if (node[1] is JsArray || node[1] is String) {
                // This node has no attributes.
                // (Note: we must check JsArray before JsObject because JSArray
                // is a subclass of JsObject.)
                attributes = new JsObject.jsify({});
                if (node.length > 1) {
                    children = node.sublist(1, node.length);
                }
            } else if (node[1] is JsObject) {
                // If node[1] is a JsObject, then node[1] contains this node's
                // attributes as a hash.
                attributes = node[1];
                if (node.length > 2) {
                    children = node.sublist(2, node.length);
                }
            }
        }

        if (children != null) {
            children.forEach((child) {
                if (child is JsArray) {
                    this.treeVisitor(child, node);
                }
            });
        }

        if (type == 'img' && attributes['src'] != null) {
            this._replaceImage(node, attributes, parent);
        } else if (type == 'a' && attributes['href'] != null) {
            this._safeLink(node, attributes, parent);
        }
    }

    /// Replace an <img> element in a JsonML tree with a placeholder icon
    /// and some explanatory text.
    void _replaceImage(JsArray imgEl, JsObject attributes, JsArray parent) {
        JsArray icon = new JsArray.from([
            'i',
            new JsObject.jsify({'class': 'fa fa-picture-o'}),
        ]);

        JsArray explanation = new JsArray.from([
            'span',
            new JsObject.jsify({'class': 'explanation'}),
            "Censored image: " + attributes['src'],
        ]);

        JsArray replacement = new JsArray.from([
            'span',
            new JsObject.jsify({'class': 'placeholder'}),
            icon,
            " ",
            explanation,
        ]);

        var parentIndex = parent.indexOf(imgEl);
        parent.removeAt(parentIndex);
        parent.insert(parentIndex, replacement);
    }

    /// Replace an <a href='...'> element in a JsonML tree with a link redirect
    /// so that the user realizes they are clicking on an external link.
    ///
    /// Note that we use a redirect rather than attaching a click event, because
    /// our HTML sanitizer blocks onclick and ng-click attributes. (Blocking
    /// is good, because these are potential XSS vectors.)
    void _safeLink(JsArray anchorEl, JsObject attributes, JsArray parent) {
        String safeHref = Uri.encodeComponent(
            // Due to linebreaks in Markdown, some links occasionally have
            // newlines inside the href!
            attributes['href'].replaceAll(new RegExp(r'\s'), '')
        );
        attributes['href'] = '/redirect/' + safeHref;
        attributes['class'] = 'external';
    }
}
