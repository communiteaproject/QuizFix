// @ts-nocheck
import React from "react";
import { Routes, Route, Link } from "react-router-dom";

import HostPanel from "./pages/HostPanel";
import TeamJoin from "./pages/TeamJoin";
import QuestionView from "./pages/QuestionView";
import LeaderboardView from "./pages/LeaderboardView";

const App: React.FC = () => {
  return (
    <div style={{ padding: "1rem" }}>
      <nav style={{ marginBottom: "1rem" }}>
        <Link to="/">Home</Link> | <Link to="/host">Host</Link> | <Link to="/join">Join</Link>
      </nav>
      <Routes>
        <Route path="/" element={<div>Welcome to Local Trivia Game</div>} />
        <Route path="/host" element={<HostPanel />} />
        <Route path="/join" element={<TeamJoin />} />
        <Route path="/question" element={<QuestionView />} />
        <Route path="/leaderboard" element={<LeaderboardView />} />
      </Routes>
    </div>
  );
};

export default App; 