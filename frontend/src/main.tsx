// @ts-nocheck

// @ts-ignore - types will resolve after dependencies are installed
import React from "react";
// @ts-ignore
import ReactDOM from "react-dom/client";
// @ts-ignore
import { BrowserRouter } from "react-router-dom";

// @ts-ignore
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root") as HTMLElement);
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
); 