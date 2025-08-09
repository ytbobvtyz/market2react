import { useState } from 'react';
import './App.css';

function App() {
  const [nmId, setNmId] = useState('');

  return (
    <div className="app">
      <h1>WB Wishlist</h1>
      <div className="search-form">
        <input
          type="text"
          value={nmId}
          onChange={(e) => setNmId(e.target.value)}
          placeholder="Введите артикул WB"
        />
        <button onClick={() => alert(`Ищем артикул: ${nmId}`)}>
          Найти
        </button>
      </div>
    </div>
  );
}

export default App;