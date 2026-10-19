// Turn a start-by time from /api/recommendations/ into "Start by 2:35 PM", or "Late, start now" once it has passed
export function formatStartBy(startBy: string) {
    const startTime = new Date(startBy);

    if (startTime.getTime() <= Date.now()) {
        return "Late, start now";
    }

    return `Start by ${startTime.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
}
