import React, { useState } from 'react'
import './styles.css'
import BarraPesquisa from "./componentes/barraDePesquisa";
import ResultadosPesquisa from "./componentes/resultadosDaPesquisa"

function App() {
  const [results, setResult] = useState([])
  const [errorMsg, setErrorMsg] = useState('')
  const [loading, setLoading] = useState(false)

  const pesquisa = async (query) => {
    setErrorMsg('')
    console.log("Pesquisando:",query)
    setLoading(true)
    try {
      const response = await fetch(`http://localhost:5000/search?q=${query}`)
      console.log(response.status)
      const data = await response.json();
      console.log('resultados:', data)

      if (!data.length) {
        setErrorMsg('Nenhum resultado encontrado')
      } else {
        setResult(data)
      }

    } catch(error) {
      console.error('Não foi possível fazer pesquisa, ERROR:',error)
      setErrorMsg('Erro ao fazer pesquisa')
      setResult([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='container'>
      <BarraPesquisa onSearch={pesquisa}/>
      {loading && <div className='loading'>Carregando...</div>}
      {errorMsg && <div className='error-Msg'>{errorMsg}</div>}
      <ResultadosPesquisa results={results}/>
    </div>
  ); 
}

export default App;
