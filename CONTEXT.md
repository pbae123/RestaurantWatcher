# CONTEXT

Glossary for RestaurantWatcher. Domain terms only — no implementation details.

## Watch Target

A single restaurant reservation page being monitored (currently: Jungsik on CatchTable). RestaurantWatcher tracks exactly one Watch Target.

## Watch Window

The explicit date range the watcher checks on every poll (currently: Nov 1–10, 2026), as opposed to the full rolling calendar the reservation site exposes. Dates outside the Watch Window are never checked or reported on.

## Party Size Watchlist

The set of party sizes the watcher checks for, per date, within the Watch Window (currently: 2 and 3). A day can be Available for one party size in the watchlist and Full for another — these are tracked independently.

## Day Slot State

The availability state of a single date within the Watch Window, for a single party size. One of:
- **Not Yet Open** — the restaurant has not opened bookings for this date yet.
- **Full** — bookings are open for this date, but no Time Slot is free.
- **Available** — bookings are open and at least one Time Slot is free.

## Time Slot

A specific bookable time (e.g. 7:30 PM) within a date that is in the Available Day Slot State, for a given party size.

## State Snapshot

The persisted record of the last known Day Slot State (and any open Time Slots) for every date in the Watch Window, across the whole Party Size Watchlist. Compared against each new poll to detect changes worth notifying on.

## Baseline Run

The first-ever run of the watcher, which has no prior State Snapshot to compare against. It records the current state as the starting point and sends a one-time "watcher is live" notification summarizing current availability, rather than treating everything as a new change.

## Change Notification

A Discord message sent when a poll's findings differ from the State Snapshot in a way that matters: a date's Day Slot State moves to Available (either from Not Yet Open or from Full), or a new Time Slot opens on an already-Available date.
