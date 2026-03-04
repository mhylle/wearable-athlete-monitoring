import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAthletes } from "@/api/hooks/useAthletes";
import { useCreateSession } from "@/api/hooks/useSessions";

const SESSION_TYPES = ["match", "training", "gym", "recovery"] as const;

export function SessionCreateForm() {
  const navigate = useNavigate();
  const { data: athletes } = useAthletes();
  const createSession = useCreateSession();

  const [athleteId, setAthleteId] = useState("");
  const [sessionType, setSessionType] = useState("");
  const [startDate, setStartDate] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endDate, setEndDate] = useState("");
  const [endTime, setEndTime] = useState("");
  const [manualDuration, setManualDuration] = useState("");
  const [notes, setNotes] = useState("");
  const [distance, setDistance] = useState("");
  const [avgHR, setAvgHR] = useState("");
  const [maxHR, setMaxHR] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  function computeDuration(): number | null {
    if (manualDuration) return Number(manualDuration);
    if (startDate && startTime && endDate && endTime) {
      const start = new Date(`${startDate}T${startTime}`);
      const end = new Date(`${endDate}T${endTime}`);
      const diffMs = end.getTime() - start.getTime();
      if (diffMs > 0) return Math.round(diffMs / 60000);
    }
    return null;
  }

  const calculatedDuration = computeDuration();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (!athleteId) {
      setError("Please select an athlete.");
      return;
    }
    if (!sessionType) {
      setError("Please select a session type.");
      return;
    }
    if (!startDate || !startTime) {
      setError("Please enter a start date and time.");
      return;
    }
    if (calculatedDuration === null || calculatedDuration <= 0) {
      setError("Please enter a valid duration or end time.");
      return;
    }

    const startISO = new Date(`${startDate}T${startTime}`).toISOString();

    createSession.mutate(
      {
        athlete_id: athleteId,
        session_type: sessionType,
        start_time: startISO,
        duration_minutes: calculatedDuration,
        source: "manual",
        ...(notes ? { notes } : {}),
        ...(distance ? { distance_meters: Number(distance) } : {}),
        ...(avgHR ? { avg_heart_rate: Number(avgHR) } : {}),
        ...(maxHR ? { max_heart_rate: Number(maxHR) } : {}),
      },
      {
        onSuccess: () => {
          setSuccess(true);
          setTimeout(() => navigate("/sessions"), 1500);
        },
        onError: (err) => {
          setError(err.message || "Failed to create session.");
        },
      }
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Log Session</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manually log a training session for an athlete.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="space-y-5 rounded-xl border border-gray-200 bg-white p-6"
      >
        {error && (
          <div role="alert" className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
        {success && (
          <div role="status" className="rounded-lg bg-green-50 px-4 py-3 text-sm text-green-700">
            Session created successfully. Redirecting...
          </div>
        )}

        {/* Athlete selector */}
        <div>
          <label htmlFor="athlete" className="block text-sm font-medium text-gray-700">
            Athlete
          </label>
          <select
            id="athlete"
            value={athleteId}
            onChange={(e) => setAthleteId(e.target.value)}
            className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">Select athlete...</option>
            {athletes?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.full_name}
              </option>
            ))}
          </select>
        </div>

        {/* Session type */}
        <div>
          <label htmlFor="sessionType" className="block text-sm font-medium text-gray-700">
            Session Type
          </label>
          <select
            id="sessionType"
            value={sessionType}
            onChange={(e) => setSessionType(e.target.value)}
            className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">Select type...</option>
            {SESSION_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Start date/time */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="startDate" className="block text-sm font-medium text-gray-700">
              Start Date
            </label>
            <input
              id="startDate"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label htmlFor="startTime" className="block text-sm font-medium text-gray-700">
              Start Time
            </label>
            <input
              id="startTime"
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
        </div>

        {/* End date/time */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="endDate" className="block text-sm font-medium text-gray-700">
              End Date
            </label>
            <input
              id="endDate"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label htmlFor="endTime" className="block text-sm font-medium text-gray-700">
              End Time
            </label>
            <input
              id="endTime"
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
        </div>

        {/* Manual duration */}
        <div>
          <label htmlFor="duration" className="block text-sm font-medium text-gray-700">
            Duration (minutes){" "}
            <span className="font-normal text-gray-400">
              {calculatedDuration !== null && !manualDuration
                ? `- auto: ${calculatedDuration} min`
                : "- or enter manually"}
            </span>
          </label>
          <input
            id="duration"
            type="number"
            min="1"
            value={manualDuration}
            onChange={(e) => setManualDuration(e.target.value)}
            placeholder="Auto-calculated from times"
            className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
          />
        </div>

        {/* Notes */}
        <div>
          <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
            Notes
          </label>
          <textarea
            id="notes"
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional session notes..."
            className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
          />
        </div>

        {/* Optional metrics */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label htmlFor="distance" className="block text-sm font-medium text-gray-700">
              Distance (m)
            </label>
            <input
              id="distance"
              type="number"
              min="0"
              value={distance}
              onChange={(e) => setDistance(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label htmlFor="avgHR" className="block text-sm font-medium text-gray-700">
              Avg HR
            </label>
            <input
              id="avgHR"
              type="number"
              min="0"
              value={avgHR}
              onChange={(e) => setAvgHR(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label htmlFor="maxHR" className="block text-sm font-medium text-gray-700">
              Max HR
            </label>
            <input
              id="maxHR"
              type="number"
              min="0"
              value={maxHR}
              onChange={(e) => setMaxHR(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={() => navigate("/sessions")}
            className="rounded-lg border border-gray-200 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createSession.isPending}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {createSession.isPending ? "Saving..." : "Log Session"}
          </button>
        </div>
      </form>
    </div>
  );
}
