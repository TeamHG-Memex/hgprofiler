import 'package:angular/angular.dart';

/// A service for holding the current page title.
@Injectable()
class TitleService {
    String title;
}

/// A component that controls the page title.
@Component(
    selector: 'title',
    template: 'HGProfiler | {{ts.title}}',
    useShadowDom: false
)
class TitleComponent {
    TitleService ts;

    TitleComponent(this.ts);
}
