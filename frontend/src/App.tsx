import './App.css'
import { useState } from "react"
import { checkHealth } from "./api/client"

function App() {
  const [status, setStatus] = useState("unknown")


  async function checkBackend() {
    const response = await checkHealth()
    setStatus(response.status)
  }

  return (
    <>
      <p>Hi</p>
      <button onClick={checkBackend}>Check backend</button>
      <p>Backend status: {status}</p>
    </>
  )
}

export default App
