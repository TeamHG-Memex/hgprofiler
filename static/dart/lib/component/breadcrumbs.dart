import 'package:angular/angular.dart';

/// A component for displaying navigation breadcrumbs.
///
/// The template for this component is nasty because ng-repeat plays
/// strange tricks on inline-block elements like the Bootstrap bread crumbs.
/// See: https://github.com/michaelbromley/angularUtils/issues/14
@Component(
    selector: 'breadcrumbs',
    templateUrl: 'packages/hgprofiler/component/breadcrumbs.html',
    useShadowDom: false
)
class BreadcrumbsComponent {
    @NgOneWay('crumbs')
    List<Breadcrumb> crumbs;
}

/// An encapsulation of a navigation breadcrumb.
class Breadcrumb {
    String name, url;

    Breadcrumb(this.name, [this.url]);
}
