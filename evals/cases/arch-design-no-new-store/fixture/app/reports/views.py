from app.reports.models import list_reports, get_report


def report_list(request):
    reports = list_reports(request.user_id)
    return render(reports)


def report_detail(request, report_id):
    report = get_report(report_id)
    return render(report)


def render(data):
    return data
