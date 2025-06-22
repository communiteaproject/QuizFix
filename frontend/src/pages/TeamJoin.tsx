// @ts-nocheck
import React, { useState } from "react";
import axios from "axios";

const TeamJoin: React.FC = () => {
  const [teamName, setTeamName] = useState("");
  const [message, setMessage] = useState("");

  const join = async () => {
    if (!teamName) return;
    const { data } = await axios.post("/api/teams", { name: teamName });
    setMessage(`Team ${data.name} registered! Share team ID: ${data.id}`);
    setTeamName("");
  };

  return (
    <div>
      <h2>Join / Create Team</h2>
      <input value={teamName} onChange={(e) => setTeamName(e.target.value)} placeholder="Team name" />
      <button onClick={join}>Register</button>
      {message && <p>{message}</p>}
    </div>
  );
};

export default TeamJoin; 