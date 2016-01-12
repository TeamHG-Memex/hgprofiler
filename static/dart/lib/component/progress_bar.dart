import 'package:angular/angular.dart';

/// A button that can display a busy state (disabled + spinner).
@Component(
    selector: 'progress-bar',
    templateUrl: 'packages/hgprofiler/component/progress_bar.html',
    useShadowDom: false
)
class ProgressBarComponent {
    @NgAttr('type')
    String type = 'default';

    @NgOneWay('progress')
    double progress;
}
