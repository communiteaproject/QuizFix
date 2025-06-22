// @ts-nocheck
import React, { useEffect, useState } from "react";
import axios from "axios";

interface LeaderboardEntry {
  team_id: number;
  team_name: string;
  points: number;
}

const LeaderboardView: React.FC = () => {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);

  const fetchLeaderboard = async () => {
    // Assume single game with ID 1 for prototype
    const { data } = await axios.get(`/api/games/1/leaderboard`);
    setEntries(data.standings);
  };

  useEffect(() => {
    fetchLeaderboard();

    const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
    ws.onmessage = (ev) => {
      const payload = JSON.parse(ev.data);
      if (payload.type === "leaderboard_update" && payload.game_id === 1) {
        setEntries(payload.standings);
      }
    };
    return () => ws.close();
  }, []);

  return (
    <div>
      <h2>Leaderboard</h2>
      <ol>
        {entries.map((e) => (
          <li key={e.team_id}>
            {e.team_name} – {e.points} pts
          </li>
        ))}
      </ol>
    </div>
  );
};

export default LeaderboardView; 