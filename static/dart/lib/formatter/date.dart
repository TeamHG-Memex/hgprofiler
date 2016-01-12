import 'package:angular/angular.dart';
import 'package:intl/intl.dart';

/// Pretty print dates encoded as ISO-8601 strings.
@Formatter(name:'isoDate')
class IsoDateFormatter {
    String call(num isoDateString, [String format='yyyy-MM-dd H:mm:ss']) {
        if (isoDateString == null) {
            return null;
        }

        DateTime isoDate = DateTime.parse(isoDateString);
        DateFormat formatter = new DateFormat(format);

        return formatter.format(isoDate);
    }
}
