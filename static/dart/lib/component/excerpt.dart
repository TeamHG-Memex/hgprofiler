import 'package:angular/angular.dart';

/// Displays an excerpt of text, optionally with certain passages highlighted.
@Component(
    selector: 'excerpt',
    templateUrl: 'packages/hgprofiler/component/excerpt.html',
    useShadowDom: false
)
class ExcerptComponent {
    @NgOneWay('text')
    List<String> text;
}
