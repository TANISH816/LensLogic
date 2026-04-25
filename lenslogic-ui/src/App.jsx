import React, { useState } from 'react';
import { Upload, Camera, Image as ImageIcon, ScanSearch } from 'lucide-react';

function App() {
  const [selectedFiles, setSelectedFiles] = useState([]);

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(files);
  };

  const startScan = () => {
    alert(`Scanning ${selectedFiles.length} photos with LensLogic AI...`);
    // This is where we will call our Spring Boot API later!
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <ScanSearch size={40} color="#4CAF50" />
        <h1 style={styles.title}>LensLogic</h1>
      </header>

      <main style={styles.main}>
        <div style={styles.card}>
          <h2>Upload Dataset</h2>
          <p>Select photos of people or nature to begin sorting.</p>
          
          <label style={styles.uploadBox}>
            <Upload size={48} />
            <p>Click to select photos</p>
            <input 
              type="file" 
              multiple 
              hidden 
              onChange={handleFileChange} 
              accept="image/*"  
            />
          </label>

          {selectedFiles.length > 0 && (
            <div style={styles.fileList}>
              <p>✅ {selectedFiles.length} files selected</p>
              <button onClick={startScan} style={styles.scanBtn}>Start AI Scan</button>
            </div>
          )}
        </div>

        <div style={styles.card}>
          <h2>Real-Time Identify</h2>
          <p>Take a selfie to find all your photos in the dataset.</p>
          <button style={styles.cameraBtn}>
            <Camera size={20} />
            Open Camera
          </button>
        </div>
      </main>
    </div>
  );
}

// Simple CSS-in-JS for now so we don't have to jump between files
const styles = {
  container: { fontFamily: 'Inter, sans-serif', backgroundColor: '#f0f2f5', minHeight: '100vh', padding: '40px' },
  header: { display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '40px', justifyContent: 'center' },
  title: { fontSize: '32px', color: '#1a1a1a' },
  main: { display: 'flex', gap: '20px', justifyContent: 'center', flexWrap: 'wrap' },
  card: { background: 'white', padding: '30px', borderRadius: '15px', width: '400px', boxShadow: '0 4px 12px rgba(0,0,0,0.05)', textAlign: 'center' },
  uploadBox: { border: '2px dashed #ccc', borderRadius: '10px', padding: '40px', display: 'block', cursor: 'pointer', margin: '20px 0', color: '#666' },
  scanBtn: { backgroundColor: '#4CAF50', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '5px', cursor: 'pointer', marginTop: '10px' },
  cameraBtn: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', width: '100%', padding: '12px', backgroundColor: '#1a1a1a', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', marginTop: '20px' }
};

export default App;