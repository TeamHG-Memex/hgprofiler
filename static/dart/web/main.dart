import 'dart:html';

import 'package:angular/angular.dart';
import 'package:angular/application_factory.dart';
import 'package:bootjack/bootjack.dart';
import 'package:dquery/dquery.dart';
import 'package:logging/logging.dart';

import 'package:hgprofiler/authentication.dart';
import 'package:hgprofiler/component/admin/background_tasks.dart';
import 'package:hgprofiler/component/admin/configuration.dart';
import 'package:hgprofiler/component/admin/index.dart';
import 'package:hgprofiler/component/breadcrumbs.dart';
import 'package:hgprofiler/component/busy_button.dart';
import 'package:hgprofiler/component/d3/grip.dart';
import 'package:hgprofiler/component/d3/heatmap.dart';
import 'package:hgprofiler/component/d3/sparkline.dart';
import 'package:hgprofiler/component/edit_select.dart';
import 'package:hgprofiler/component/edit_text.dart';
import 'package:hgprofiler/component/excerpt.dart';
import 'package:hgprofiler/component/group/list.dart';
import 'package:hgprofiler/component/home.dart';
import 'package:hgprofiler/component/login.dart';
import 'package:hgprofiler/component/markdown.dart';
import 'package:hgprofiler/component/masonry.dart';
import 'package:hgprofiler/component/modal.dart';
import 'package:hgprofiler/component/nav.dart';
import 'package:hgprofiler/component/pager.dart';
import 'package:hgprofiler/component/progress_bar.dart';
import 'package:hgprofiler/component/site.dart';
import 'package:hgprofiler/component/sort.dart';
import 'package:hgprofiler/component/title.dart';
import 'package:hgprofiler/component/user/list.dart';
import 'package:hgprofiler/component/user/view.dart';
import 'package:hgprofiler/component/username.dart';
import 'package:hgprofiler/decorator/current_route.dart';
import 'package:hgprofiler/formatter/date.dart';
import 'package:hgprofiler/formatter/default.dart';
import 'package:hgprofiler/formatter/number.dart';
import 'package:hgprofiler/rest_api.dart';
import 'package:hgprofiler/router.dart';
import 'package:hgprofiler/sse.dart';

/// The main application module.
class HGProfilerApplication extends Module {
    HGProfilerApplication({Level logLevel: Level.OFF}) {
        Logger.root.level = logLevel;
        Logger.root.onRecord.listen((LogRecord rec) {
            print('${rec.time} [${rec.level.name}] ${rec.message}');
        });

        NodeValidatorBuilder nodeValidator = new NodeValidatorBuilder.common()
            ..allowHtml5()
            ..allowElement('a', attributes: ['href'])
            ..allowElement('i', attributes: ['class'])
            ..allowElement('img', attributes: ['alt', 'src']);

        bind(AdminIndexComponent);
        bind(AuthenticationController);
        bind(BackgroundTasksComponent);
        bind(BreadcrumbsComponent);
        bind(BusyButtonComponent);
        bind(ConfigurationListComponent);
        bind(CurrentRoute);
        bind(DefaultFormatter);
        bind(EditSelectComponent);
        bind(EditTextComponent);
        bind(ExcerptComponent);
        bind(GripComponent);
        bind(GroupListComponent);
        bind(HeatmapComponent);
        bind(HomeComponent);
        bind(IsoDateFormatter);
        bind(LargeNumberFormatter);
        bind(LoginComponent);
        bind(MarkdownComponent);
        bind(MasonryComponent);
        bind(ModalComponent);
        bind(NavComponent);
        bind(PagerComponent);
        bind(ProgressBarComponent);
        bind(NodeValidator, toValue: nodeValidator);
        bind(RestApiController);
        bind(RouteInitializerFn, toImplementation: HGProfilerRouteInitializer);
        bind(SiteComponent);
        bind(SortComponent);
        bind(SparklineComponent);
        bind(SseController);
        bind(TitleComponent);
        bind(TitleService);
        bind(UserComponent);
        bind(UserListComponent);
        bind(UsernameComponent);
    }
}

/// The application entry point.
///
/// This instantiates and runs the application.
void main() {
    // Register Bootjack components.
    Collapse.use();
    Dropdown.use();
    Modal.use();
    Transition.use();

    // Create main application.
    applicationFactory()
        .addModule(new HGProfilerApplication())
        .run();
}
