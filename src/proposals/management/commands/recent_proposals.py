import logging
from datetime import datetime, timedelta
from io import StringIO

from tabulate import tabulate
import pytz

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from proposals.models import TalkProposal, TutorialProposal

logger = logging.getLogger(__file__)


def str_stripper(s, max_len=32, ellipsis='...'):
    if len(s) > max_len:
        return s[:max_len - len(ellipsis)] + ellipsis
    else:
        return s


def proposal_summary(queryset):
    table = []
    for p in queryset:
        table.append((
            str_stripper(p.get_category_display(), 16),
            str_stripper(p.get_python_level_display(), 16),
            p.title
        ))
    return tabulate(
        table,
        ['Category', 'Python Level', 'Title'],
        tablefmt='simple'
    )


class Command(BaseCommand):
    help = "Summarize the recent proposal submits."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg = StringIO()

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            metavar='N',
            type=int,
            default=3,
            help='Collect proposals submitted in the latest N days.'
        )
        parser.add_argument(
            '--hour',
            metavar='H',
            type=int,
            default=21,
            help="""
            Set the hour to cut the day shift. For example, if 21 O\'clock in
            is set, it finds proposals submitted between today-N 21:00 to today
            21:00. An error will be raised if the given hour time has not come.
            """
        )
        parser.add_argument(
            '--mailto',
            metavar='ADDR',
            type=str,
            default=None,
            help="""If set, mail the stdout to the given address."""
        )

    def handle(self, *args, **options):
        recent_lookup = self.create_datetime_range_lookup(*args, **options)
        recent_talks = TalkProposal.objects.filter(recent_lookup)
        recent_tutorials = TutorialProposal.objects.filter(recent_lookup)
        self.msg.write(
            'Got total {:d} new proposals\n'.format(
                recent_talks.count() + recent_tutorials.count()
            ))
        if not recent_talks.exists() and not recent_tutorials.exists():
            self.cry()
        else:
            self.summary(recent_talks, recent_tutorials)
        self.report(options['mailto'])

    def summary(self, recent_talks, recent_tutorials):
        if recent_talks:
            self.msg.write('\n\nTalks:\n')
            self.msg.write(proposal_summary(recent_talks))

        if recent_tutorials:
            self.msg.write('\n\nTutorials:\n')
            self.msg.write(proposal_summary(recent_tutorials))

    def report(self, mailto=None):
        if mailto:
            pass
        else:
            self.stdout.write(self.msg.getvalue())

    def create_datetime_range_lookup(self, *args, **options):
        """Create valid recent datetime range and return a lookup Q object"""
        utc_tz = pytz.UTC
        taiwan_tz = pytz.timezone('Asia/Taipei')
        recent_days = options['days']
        if recent_days <= 0:
            raise CommandError(
                'Given number of days %d is not a positive number'
                % recent_days
            )
        day_shift_hour = options['hour']
        today_utc_dt = utc_tz.fromutc(datetime.utcnow())
        # To find the datetime range in Taiwan timezone
        #   today-N H:00 to today H:00
        try:
            today_dt = taiwan_tz.normalize(today_utc_dt).replace(
                hour=day_shift_hour, minute=0, second=0, microsecond=0
            )
        except ValueError as e:
            raise CommandError(
                'Given hour %d is invalid' % day_shift_hour
            ) from e
        if today_dt > today_utc_dt:
            raise CommandError(
                "Today's datetime {:%Y-%m-%d %H:%M} ({!s}) is yet present"
                .format(today_dt, taiwan_tz)
            )
        earliest_dt = today_dt - timedelta(days=recent_days)
        self.msg.write(
            'Recent {:d} days proposals \n'
            'From {:%Y-%m-%d %H:%M} to {:%Y-%m-%d %H:%M} (timezone: {!s})\n'
            .format(recent_days, earliest_dt, today_dt, taiwan_tz)
        )
        recent_lookup = Q(
            created_at__gte=earliest_dt,
            created_at__lt=today_dt,
            cancelled=False,
        )
        return recent_lookup

    def cry(self):
        self.msg.write(
            'No proposals are recently submitted\n'
            '◢▆▅▄▃ 崩╰(〒皿〒)╯潰 ▃▄▅▆◣\n'
        )


