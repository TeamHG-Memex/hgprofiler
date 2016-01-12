import 'package:intl/intl.dart';

/// Generate month/year labels for a series of months, starting ``numMonths``
/// ago and ending in the current month.
List<String> monthLabelsToNow(int numMonths) {
    List<String> labels = new List<String>();
    DateTime today = new DateTime.now();
    DateFormat monthFormat = new DateFormat('yMMM');

    for (int i = numMonths; i >= 0; i--) {
        num year = i > today.month ? today.year - 1 : today.year;
        DateTime month = new DateTime(year, (today.month - i + 12) % 12);
        labels.add(monthFormat.format(month));
    }

    return labels;
}
