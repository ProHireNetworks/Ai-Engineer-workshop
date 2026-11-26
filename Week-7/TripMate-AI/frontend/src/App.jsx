
import { useState } from "react";
import "./App.css";

function App() {
  const [formData, setFormData] = useState({
    origin: "Hyderabad",
    destination: "Goa",
    start_date: "2026-12-10",
    end_date: "2026-12-13",
    travelers: 2,
    budget: 15000,
    currency: "INR",
    travel_style: "balanced",
    interests: "beaches, local food, sightseeing",
    special_requirements: "",
  });

  const [itinerary, setItinerary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setItinerary(null);

    try {
  const response = await fetch(
    `${import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"}/api/plan-trip`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...formData,
        travelers: Number(formData.travelers),
        budget: Number(formData.budget),
        interests: formData.interests
          .split(",")
          .map((interest) => interest.trim())
          .filter(Boolean),
        special_requirements:
          formData.special_requirements || null,
      }),
    }
  );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to generate your trip."
        );
      }

      setItinerary(data);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="hero">
        <div className="hero-content">
          <span className="brand">✈ TripMate AI</span>

          <h1>Your Journey, Powered by AI</h1>

          <p>
            Plan smarter trips with personalized itineraries,
            destination research and budget analysis.
          </p>
        </div>
      </header>

      <main className="container">
        <section className="form-section">
          <div className="section-heading">
            <h2>Plan Your Next Adventure</h2>
            <p>Tell us your travel preferences.</p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label>Starting From</label>
                <input
                  name="origin"
                  value={formData.origin}
                  onChange={handleChange}
                  placeholder="Enter origin"
                  required
                />
              </div>

              <div className="form-group">
                <label>Destination</label>
                <input
                  name="destination"
                  value={formData.destination}
                  onChange={handleChange}
                  placeholder="Enter destination"
                  required
                />
              </div>

              <div className="form-group">
                <label>Start Date</label>
                <input
                  type="date"
                  name="start_date"
                  value={formData.start_date}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>End Date</label>
                <input
                  type="date"
                  name="end_date"
                  value={formData.end_date}
                  onChange={handleChange}
                  min={formData.start_date}
                  required
                />
              </div>

              <div className="form-group">
                <label>Number of Travelers</label>
                <input
                  type="number"
                  name="travelers"
                  min="1"
                  max="20"
                  value={formData.travelers}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Total Budget (₹)</label>
                <input
                  type="number"
                  name="budget"
                  min="1"
                  value={formData.budget}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Travel Style</label>
                <select
                  name="travel_style"
                  value={formData.travel_style}
                  onChange={handleChange}
                >
                  <option value="budget">Budget</option>
                  <option value="balanced">Balanced</option>
                  <option value="luxury">Luxury</option>
                  <option value="adventure">Adventure</option>
                </select>
              </div>

              <div className="form-group">
                <label>Currency</label>
                <select
                  name="currency"
                  value={formData.currency}
                  onChange={handleChange}
                >
                  <option value="INR">INR (₹)</option>
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                </select>
              </div>

              <div className="form-group full-width">
                <label>Interests</label>
                <input
                  name="interests"
                  value={formData.interests}
                  onChange={handleChange}
                  placeholder="Beaches, food, adventure, history"
                />
                <small>Separate interests using commas.</small>
              </div>

              <div className="form-group full-width">
                <label>Special Requirements (Optional)</label>
                <textarea
                  name="special_requirements"
                  value={formData.special_requirements}
                  onChange={handleChange}
                  placeholder="Any special travel requirements?"
                  rows="3"
                />
              </div>
            </div>

            <button
              type="submit"
              className="generate-button"
              disabled={loading}
            >
              {loading
                ? "Generating Your Trip..."
                : "✈ Generate My Trip"}
            </button>
          </form>
        </section>

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {loading && (
          <p className="loading-message">
            Our AI agents are researching and planning your trip...
          </p>
        )}

        {/* Generated Travel Results */}
        {itinerary && (
          <section className="results-section">
            <div className="section-heading">
              <h2>Your AI-Generated Travel Plan</h2>
              <p>{itinerary.itinerary.destination}</p>
            </div>

            {/* Destination Research */}
            <div className="research-card">
              <h3>Destination Research</h3>
              <p>{itinerary.research.overview}</p>

              <h4>Popular Attractions</h4>
              <ul>
                {itinerary.research.attractions?.map(
                  (item, index) => (
                    <li key={index}>{item}</li>
                  )
                )}
              </ul>

              <h4>Famous Local Foods</h4>
              <ul>
                {itinerary.research.local_foods?.map(
                  (item, index) => (
                    <li key={index}>{item}</li>
                  )
                )}
              </ul>

              <h4>Transportation</h4>
              <ul>
                {itinerary.research.transportation?.map(
                  (item, index) => (
                    <li key={index}>{item}</li>
                  )
                )}
              </ul>

              <h4>Travel Tips</h4>
              <ul>
                {itinerary.research.travel_tips?.map(
                  (item, index) => (
                    <li key={index}>{item}</li>
                  )
                )}
              </ul>

              <h4>Important Notes</h4>
              <ul>
                {itinerary.research.important_notes?.map(
                  (item, index) => (
                    <li key={index}>{item}</li>
                  )
                )}
              </ul>
            </div>

            {/* Travel Itinerary */}
            <h2 className="days-heading">
              Your Daily Travel Plan
            </h2>

            <div className="summary-card">
              <h3>Trip Overview</h3>
              <p>{itinerary.itinerary.summary}</p>

              <h3>
                Estimated Cost: {itinerary.itinerary.currency}{" "}
                {Number(
                  itinerary.itinerary.total_estimated_cost
                ).toLocaleString()}
              </h3>
            </div>

            {itinerary.itinerary.days?.map((day) => (
              <div className="day-card" key={day.day_number}>
                <h3>
                  Day {day.day_number}: {day.title}
                </h3>

                <p className="day-date">{day.date}</p>

                {day.activities?.map((activity, index) => (
                  <div className="activity" key={index}>
                    <h4>{activity.title}</h4>
                    <p>{activity.description}</p>

                    <p>
                      <strong>Time:</strong> {activity.time}
                    </p>

                    {activity.location && (
                      <p>
                        <strong>Location:</strong>{" "}
                        {activity.location}
                      </p>
                    )}

                    <p>
                      <strong>Estimated Cost:</strong>{" "}
                      {itinerary.itinerary.currency}{" "}
                      {Number(
                        activity.estimated_cost
                      ).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            ))}

            {/* Budget Analysis */}
            <div className="budget-card">
              <h3>Budget Analysis</h3>

              <p>
                <strong>Total Budget:</strong>{" "}
                {Number(
                  itinerary.budget_analysis.total_budget
                ).toLocaleString()}{" "}
                {itinerary.itinerary.currency}
              </p>

              <p>
                <strong>Estimated Cost:</strong>{" "}
                {Number(
                  itinerary.budget_analysis.estimated_total_cost
                ).toLocaleString()}{" "}
                {itinerary.itinerary.currency}
              </p>

              <p>
                <strong>Remaining Budget:</strong>{" "}
                {Number(
                  itinerary.budget_analysis.remaining_budget
                ).toLocaleString()}{" "}
                {itinerary.itinerary.currency}
              </p>

              <h4>
                Budget Status:{" "}
                <span
                  className={`budget-status ${
                    itinerary.budget_analysis.within_budget
                      ? ""
                      : "over-budget"
                  }`}
                >
                  {itinerary.budget_analysis.within_budget
                    ? "Within Budget"
                    : "Over Budget"}
                </span>
              </h4>

              <h4>Recommendations</h4>
              <ul>
                {itinerary.budget_analysis.recommendations?.map(
                  (item, index) => (
                    <li key={index}>{item}</li>
                  )
                )}
              </ul>
            </div>
          </section>
        )}
      </main>

      <footer>
        <p>
          TripMate AI | Your Smart Travel Planning Assistant
        </p>
      </footer>
    </div>
  );
}

export default App;
