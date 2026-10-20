// Turn a start-by time from /api/recommendations/ into "Start by 2:35 PM", or "Late, start now" once it has passed
export function formatStartBy(startBy: string) {
    const startTime = new Date(startBy);

    if (startTime.getTime() <= Date.now()) {
        return "Late, start now";
    }

    return `Start by ${formatDayAndTime(startTime)}`;
}


// Show "6:14 PM" for today, "tomorrow 6:14 PM", or "Wed 6:14 PM" for later days, in the browser's time zone
function formatDayAndTime(time: Date) {
    const clock = time.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

    // Count calendar days between today and the start time, ignoring the time of day
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const startDay = new Date(time);
    startDay.setHours(0, 0, 0, 0);

    const daysAway = Math.round((startDay.getTime() - today.getTime()) / 86400000);

    if (daysAway === 0) {
        return clock;
    }

    if (daysAway === 1) {
        return `tomorrow ${clock}`;
    }

    return `${time.toLocaleDateString([], { weekday: "short" })} ${clock}`;
}
