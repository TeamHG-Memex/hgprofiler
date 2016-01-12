import 'package:angular/angular.dart';

/// A formatter for large numbers.
///
/// This displays numbers with unit suffixes, e.g. 25K instead of 25000. Numbers
/// under 1000 are displayed as is.
@Formatter(name:'largeNumber')
class LargeNumberFormatter {
    static final LinkedHashMap<String, num> suffixes = {
        1e12: 'T',
        1e9:  'B',
        1e6:  'M',
        1e3:  'K',
    };

    String call(num numberToFormat, [num decimals=0]) {
        if (numberToFormat == null) {
            return null;
        }

        for (num size in LargeNumberFormatter.suffixes.keys) {
            if (numberToFormat > size) {
                num round = (numberToFormat / size).toStringAsFixed(decimals);
                String suffix = LargeNumberFormatter.suffixes[size];
                return '$round$suffix';
            }
        }

        return numberToFormat;
    }
}
