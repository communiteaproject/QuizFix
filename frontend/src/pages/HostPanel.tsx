// @ts-nocheck
import React, { useEffect, useState } from "react";
import axios from "axios";

interface Game {
  id: number;
  title: string;
  phase: string;
}

const HOST_TOKEN = "changeme"; // must match backend HOST_TOKEN env

const HostPanel: React.FC = () => {
  const [games, setGames] = useState<Game[]>([]);
  const [title, setTitle] = useState("");
  const [broadcastId, setBroadcastId] = useState("");
  const [selectedGameId, setSelectedGameId] = useState<number | null>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [newRoundId, setNewRoundId] = useState(0);
  const [newOrder, setNewOrder] = useState(1);
  const [newText, setNewText] = useState("");
  const [newAnswer, setNewAnswer] = useState("");
  const [mediaFile, setMediaFile] = useState<File | null>(null);

  const fetchGames = async () => {
    const { data } = await axios.get<Game[]>("/api/games");
    setGames(Array.isArray(data) ? data : [data]);
  };

  const createGame = async () => {
    if (!title) return;
    await axios.post("/api/games", { title });
    setTitle("");
    fetchGames();
  };

  const broadcastQuestion = async (id?: string) => {
    const qid = id || broadcastId;
    if (!qid) return;
    await axios.post(`/api/questions/${qid}/broadcast`, {}, { headers: { "X-Host-Token": HOST_TOKEN } });
    setBroadcastId("");
  };

  const loadQuestions = async (gameId: number) => {
    const { data } = await axios.get(`/api/games/${gameId}/questions`);
    setQuestions(data);
  };

  const handleSelectGame = (gameId: number) => {
    setSelectedGameId(gameId);
    loadQuestions(gameId);
  };

  const createQuestion = async () => {
    if (!selectedGameId) return;
    let media_url = "";
    if (mediaFile) {
      const formData = new FormData();
      formData.append("file", mediaFile);
      const res = await axios.post("/api/media/upload", formData, {
        headers: { "X-Host-Token": HOST_TOKEN, "Content-Type": "multipart/form-data" },
      });
      media_url = res.data.url;
    }

    const round_id = newRoundId;

    await axios.post(
      "/api/questions",
      {
        text: newText,
        answer: newAnswer,
        media_url,
        order: newOrder,
        round_id,
      },
      { headers: { "X-Host-Token": HOST_TOKEN } }
    );

    setNewText("");
    setNewAnswer("");
    setMediaFile(null);
    loadQuestions(selectedGameId);
  };

  useEffect(() => {
    fetchGames();

    const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
    ws.onmessage = (ev) => {
      const payload = JSON.parse(ev.data);
      if (payload.type === "phase_update") {
        setGames((prev) =>
          prev.map((g) => (g.id === payload.game_id ? { ...g, phase: payload.phase } : g))
        );
      }
    };
    return () => ws.close();
  }, []);

  return (
    <div>
      <h2>Host Panel</h2>
      <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Game title" />
      <button onClick={createGame}>Create Game</button>

      <h3>Existing Games</h3>
      <ul>
        {games.map((g) => (
          <li key={g.id}>
            <button onClick={() => handleSelectGame(g.id)} style={{ marginRight: 8 }}>
              Select
            </button>
            {g.title} - phase: {g.phase}
            {selectedGameId === g.id && <strong> (selected)</strong>}
          </li>
        ))}
      </ul>

      {selectedGameId && (
        <>
          <h3>Questions for Game {selectedGameId}</h3>
          <ul>
            {questions.map((q) => (
              <li key={q.id}>
                Round {q.round_id} - Q{q.order}: {q.text?.slice(0, 40)}...
                <button
                  style={{ marginLeft: 8 }}
                  onClick={() => broadcastQuestion(q.id.toString())}
                >
                  Broadcast
                </button>
              </li>
            ))}
          </ul>

          <h3>Create Question</h3>
          <div className="mb-2">
            <label className="form-label">Round ID</label>
            <input
              type="number"
              className="form-control"
              value={newRoundId}
              onChange={(e) => setNewRoundId(parseInt(e.target.value))}
            />
          </div>
          <div className="mb-2">
            <label className="form-label">Order (1-10)</label>
            <input
              type="number"
              className="form-control"
              value={newOrder}
              onChange={(e) => setNewOrder(parseInt(e.target.value))}
            />
          </div>
          <div className="mb-2">
            <label className="form-label">Question Text</label>
            <textarea className="form-control" value={newText} onChange={(e) => setNewText(e.target.value)} />
          </div>
          <div className="mb-2">
            <label className="form-label">Answer</label>
            <input className="form-control" value={newAnswer} onChange={(e) => setNewAnswer(e.target.value)} />
          </div>
          <div className="mb-2">
            <label className="form-label">Media File (optional)</label>
            <input type="file" className="form-control" onChange={(e) => setMediaFile(e.target.files?.[0] || null)} />
          </div>
          <button className="btn btn-primary" onClick={createQuestion}>Create Question</button>
        </>
      )}
    </div>
  );
};

export default HostPanel; 