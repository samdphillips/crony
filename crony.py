
import collections
import time

from datetime import datetime, timedelta

class _AnyTime(object):
    is_anytime = True

    def __init__(self, min, max):
        self._min = min
        self._max = max

    def __contains__(self, value):
        return True

    def first(self):
        return self._min

    def next_greater(self, state, value):
        if value == self._max:
            return None
        return value + 1


class _Times(list):
    is_anytime = False

    def first(self):
        return self[0]

    def next_greater(self, state, value):
        for v in self:
            if value < v:
                return v
        return None


class _WeekdayTimes(object):
    is_anytime = False

    def __init__(self, day_times, weekday_times):
        self._day  = day_times
        self._wday = weekday_times

    def __contains__(self, dt):
        if self._day.is_anytime and self._wday.is_anytime:
            return True
        if not self._day.is_anytime and dt.day in self._day:
            return True
        wday = (dt.weekday() + 1) % 7
        if not self._wday.is_anytime and wday in self._wday:
            return True
        return False

    def first(self):
        if self._wday.is_anytime:
            return self._day.first()
        # conservatively always return the first day of the month
        return 1

    def _next_wday(self, state, value):
        try:
            dt = state.as_datetime()
        except ValueError:
            return None

        wday = (dt.weekday() + 1) % 7
        next = self._wday.next_greater(state, wday)
        if next is None:
            next = self._wday.first()

        days = (next - wday) % 7
        if days == 0:
            days = 7
        new_dt = dt + timedelta(days=days)

        if new_dt.month != dt.month:
            return None
        return new_dt.day


    def next_greater(self, state, value):
        if self._wday.is_anytime:
            return self._day.next_greater(state, value)

        if self._day.is_anytime:
            return self._next_wday(state, value)

        next_wday = self._next_wday(state,value)
        next_day  = self._day.next_greater(state, value)

        if next_wday is None:
            return next_day
        if next_day is None:
            return next_wday

        print 'foo', next_wday, next_day
        return min(next_wday, next_day)


__SearchState = collections.namedtuple('__SearchState', 'year month day hour minute')
class _SearchState(__SearchState):
    def reset_fields(self, ranges, reset_names):
        if reset_names == []:
            return self

        update = dict([(name, getattr(ranges, name).first()) for name in reset_names])
        return self._replace(**update)

    def update(self, field, value):
        return self._replace(**{field: value})

    def as_datetime(self):
        return datetime(*self)


class CronSchedule(object):
    def __init__(self, schedule):
        min, hour, dom, mon, dow = schedule.split()
        self.schedule_string = schedule
        self.minute  = self.parse_range(min,  0, 59)
        self.hour    = self.parse_range(hour, 0, 23)
        self.month   = self.parse_range(mon,  1, 12)
        # XXX: fix this
        # self.year    = self.parse_range('*',  0, 9999)
        self.year    = self.parse_range('*',  0, 2020)

        day      = self.parse_range(dom,  1, 31)
        weekday  = self.parse_range(dow,  0, 6)
        self.day = _WeekdayTimes(day, weekday)

    def parse_range(self, spec, min, max):
        if spec == '*':
            return _AnyTime(min, max)

        times = _Times()
        for t in spec.split(','):
            if t.isdigit():
                times.append(int(t))
            else:
                raise Exception
        return times

    def coerce_datetime(self, dt):
        if isinstance(dt, datetime):
            return dt
        return dt.as_datetime()

    def is_in_schedule(self, dt):
        try:
            dt = self.coerce_datetime(dt)
            return (dt.minute in self.minute and
                    dt.hour   in self.hour   and
                    dt.month  in self.month  and
                    dt        in self.day)
        except ValueError:
            return False

    def next_after(self, dt):
        next = dt.replace(microsecond=0, second=0)
        next = next + timedelta(minutes=1)
        fields = ['minute', 'hour', 'day', 'month', 'year']
        state = _SearchState(next.year, next.month, next.day, next.hour, next.minute)

        print self.schedule_string

        while not self.is_in_schedule(state):
            reset = []
            for field in fields:
                range = getattr(self, field)
                value = getattr(state, field)
                state = state.reset_fields(self, reset)
                next_value = range.next_greater(state, value)
                print "%-15s %-10s %70s %s" % (self.schedule_string, field, state, next_value)
                if next_value is not None:
                    state = state.update(field, next_value)
                    break
                if field == 'year':
                    raise Exception('hello year 10000')
                reset.append(field)


        print state
        next = state.as_datetime()
        print next
        print
        return next


assert (CronSchedule('* * * * *').next_after(datetime(2014, 1, 1)) ==
        datetime(2014, 1, 1, 0, 1, 0))

assert (CronSchedule('* * * * *').next_after(datetime(2014, 1, 1, 0, 0, 30)) ==
        datetime(2014, 1, 1, 0, 1, 0))

assert (CronSchedule('30 * * * *').next_after(datetime(2014, 1, 1)) ==
        datetime(2014, 1, 1, 0, 30, 0))

assert (CronSchedule('30 * * * *').next_after(datetime(2014, 1, 1, 0, 31)) ==
        datetime(2014, 1, 1, 1, 30, 0))

assert (CronSchedule('0 12 * * *').next_after(datetime(2014, 1, 1, 0, 0)) ==
        datetime(2014, 1, 1, 12, 0, 0))

assert (CronSchedule('0 12 * * *').next_after(datetime(2014, 1, 31, 13, 0)) ==
        datetime(2014, 2, 1, 12, 0, 0))

assert (CronSchedule('0 * 1 4 *').next_after(datetime(2014, 1, 1)) ==
        datetime(2014, 4, 1, 0, 0, 0))

assert (CronSchedule('0 * 1 4 *').next_after(datetime(2014, 1, 15)) ==
        datetime(2014, 4, 1, 0, 0, 0))

assert (CronSchedule('0 * 1 4 *').next_after(datetime(2014, 4, 16)) ==
        datetime(2015, 4, 1, 0, 0, 0))

assert (CronSchedule('0 0 29 2 *').next_after(datetime(2014, 1, 1)) ==
        datetime(2016, 2, 29, 0, 0, 0))

# leap years and wednesdays in february
assert (CronSchedule('0 0 29 2 3').next_after(datetime(2014, 1, 2)) ==
        datetime(2014, 2, 5, 0, 0, 0))

assert (CronSchedule('0 0 29 2 3').next_after(datetime(2014, 3, 1)) ==
        datetime(2015, 2, 4, 0, 0, 0))

assert (CronSchedule('0 0 * * 3').next_after(datetime(2014, 1, 2)) ==
        datetime(2014, 1, 8, 0, 0, 0))

