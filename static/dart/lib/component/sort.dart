import 'package:angular/angular.dart';

/// A component used for sorting a table column.
@Component(
    selector: 'sort',
    templateUrl: 'packages/hgprofiler/component/sort.html',
    useShadowDom: false
)
class SortComponent {
    @NgOneWay('href')
    String href;

    @NgAttr('title')
    String title;

    @NgOneWay('active')
    bool active = false;

    @NgOneWay('descending')
    bool descending = true;

    /// Return a string for the title attribute.
    String getTitle() {
        if (title != null) {
            return title;
        } else {
            String dir = (!active || !descending) ? 'descending' : 'ascending';
            return 'Click to sort $dir.';
        }
    }
}
