// @ts-nocheck
import React, { useEffect, useState, useRef } from "react";
import axios from "axios";

interface Question {
  id: number;
  text: string;
  media_url?: string;
  order: number;
}

const QuestionView: React.FC = () => {
  const [question, setQuestion] = useState<Question | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
    ws.onmessage = (ev) => {
      const payload = JSON.parse(ev.data);
      if (payload.type === "question") {
        setQuestion(payload.question);
      }
    };
    return () => ws.close();
  }, []);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [question]);

  if (!question) return <div>Waiting for next question…</div>;

  return (
    <div>
      <h2>Question {question.order}</h2>
      <p>{question.text}</p>
      {question.media_url && (
        question.media_url.match(/\.mp4$/)
          ? <video controls style={{ maxWidth: "100%" }} src={question.media_url} />
          : <img src={question.media_url} alt="media" style={{ maxWidth: "100%" }} />
      )}
      <div ref={bottomRef} />
    </div>
  );
};

export default QuestionView; 