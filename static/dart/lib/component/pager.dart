import 'dart:html';
import 'dart:math';

import 'package:angular/angular.dart';
import 'package:hgprofiler/rest_api.dart';

/// A component that displays pagination controls.
@Component(
    selector: 'pager',
    templateUrl: 'packages/hgprofiler/component/pager.html',
    useShadowDom: false
)
class PagerComponent {
    @NgOneWay('pager')
    Pager pager;

    @NgOneWay('disabled')
    bool pagerDisabled;

    /// Disables default click behavior when the parent <li> is disabled.
    void anchorClick(Event e) {
        Element parent = e.target.parentNode;

        while (!(parent is LIElement)) {
            parent = parent.parentNode;
        }

        if (parent.classes.contains('disabled')) {
            e.preventDefault();
            e.stopPropagation();
        }
    }
}

/// Handles paging logic, such as figuring out how many pages to display,
/// hrefs for each page, which buttons to disable, etc.
class Pager {
    Page first, next, previous, last;
    List<Page> pages;
    int currentPage, maxPages, resultsPerPage, totalResults;
    Function getHref;

    int get startingAt => totalResults == 0 ?
                          totalResults :
                          (currentPage - 1) * resultsPerPage + 1;
    int get endingAt => min(currentPage * resultsPerPage, totalResults);

    /// Constructor.
    Pager(this.totalResults, this.currentPage,
          {this.maxPages: 10, this.resultsPerPage: 10, getHref: null}) {

        this.getHref = getHref != null ? getHref : this._defaultGetHref;
        this._makePages();
    }

    /// A default href getter that should work for most use cases.
    String _defaultGetHref(int pageNum) {
        Uri uri = Uri.parse(window.location.toString());
        Map queryParameters = new Map.from(uri.queryParameters);

        if (pageNum == 1 && queryParameters.containsKey('page')) {
            queryParameters.remove('page');
        } else {
            queryParameters['page'] = pageNum.toString();
        }

        return urlWithArgs(uri.path, queryParameters);
    }

    /// Initializes all of the pages.
    void _makePages() {
        int totalPages = (this.totalResults / this.resultsPerPage).ceil();
        int shownPages = min(totalPages, this.maxPages);

        this.first = new Page(null, this.getHref(1));
        this.previous = new Page(null, this.getHref(this.currentPage - 1));
        this.next = new Page(null, this.getHref(this.currentPage + 1));
        this.last = new Page(null, this.getHref(totalPages));

        if (this.currentPage == 1) {
            this.previous.disabled = true;
        }

        if (this.currentPage == totalPages) {
            this.next.disabled = true;
        }

        int startPage = this.currentPage - (shownPages / 2).ceil();

        if (startPage < 1) {
            startPage = 1;
        } else if (startPage > totalPages - shownPages + 1) {
            startPage = totalPages - shownPages + 1;
        }

        this.pages = new List<Page>.generate(
            shownPages,
            (index) {
                int pageNumber = index + startPage;
                String href = this.getHref(pageNumber);
                Page page = new Page(pageNumber, href);

                if (pageNumber == this.currentPage) {
                    page.disabled = true;
                }

                return page;
            }
        );
    }
}

/// A single page within a pager.
class Page {
    int number;
    String href;
    bool disabled = false;

    Page(this.number, this.href);
}

