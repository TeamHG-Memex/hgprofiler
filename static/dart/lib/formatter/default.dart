import 'package:angular/angular.dart';
import 'package:intl/intl.dart';

/// Display a default value when a variable is null or empty.
@Formatter(name:'default')
class DefaultFormatter {
    String call(dynamic value, String defaultValue) {
        if (value == null || value is String && value.isEmpty) {
            return defaultValue;
        } else  {
            return value;
        }
    }
}
