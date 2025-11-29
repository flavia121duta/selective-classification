import React, { useState, useEffect } from "react";
import upload_icon from "./assets/upload.png";
import beauty_products from "./assets/beauty-products.jpg";
import styles from './App.module.css';

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [fileName, setFileName] = useState("");
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  const API_BASE_URL = "https://selective-classification.onrender.com";
  // const LOCAL_API_BASE_URL = "http://localhost:8000";


  // SSE for progress
  useEffect(() => {
    const eventSource = new EventSource(`${API_BASE_URL}/progress`);
    eventSource.onmessage = (event) => {
      setProgress(Number(event.data));
    };
    return () => eventSource.close();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setFileName(f.name);
      setDownloadUrl(null);
      setProgress(0);
    }
  };

  const uploadFile = async () => {
    if (!file) return;
    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE_URL}/classify`, {
        method: "POST",
        body: formData,
      });
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      setDownloadUrl(url);
    } catch (error) {
      alert("Error processing file");
      console.error(error);
    }

    setLoading(false);
  };

  return (
    <div className={styles.wrapper}>

      <div className={styles.container}>
        <h1>Selective Product Classifier</h1>

        <label className={styles.button}>
          <img src={upload_icon} alt="upload icon" width={20} height={20} style={{ marginRight: 8 }} />
          Upload Excel
          <input type="file" accept=".xlsx" onChange={handleFileChange} style={{ display: "none" }} />
        </label>

        {fileName && <p>Selected file: <strong>{fileName}</strong></p>}

        <br />

        {
          (loading && downloadUrl == null) && <p>Processing data, please wait...</p>
        }

        {
          (!loading && downloadUrl == null) &&
          <button className={styles.submit} onClick={uploadFile} disabled={!file || loading}>
            Classify Products
          </button>
        }


        {loading && (
          <div style={{ marginTop: 10 }}>
            <p>Progress: {progress}%</p>

            <div className={styles.progressBarOuter}>
              <div
                className={styles.progressBarInner}
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        )}


        {downloadUrl && (
          <a href={downloadUrl} download="produse_clasificate.xlsx" className={styles.download}>
            Download Selective
          </a>
        )}
      </div>

      <img
        src={beauty_products}
        alt="Beauty Products"
        className={styles["beauty-products"]}
      />

      {/* <div className={styles.instructionBox}>
        <p>Upload an Excel file that has the following structure:</p>
        <ol className={styles.fieldList}>
          <li>Retailer</li>
          <li>ProductID</li>
          <li>*EAN</li>
          <li>*ProductName</li>
          <li>*CategoryName</li>
          <li>*CategoryName_1</li>
          <li>*SubcategorName</li>
          <li>*TypeName</li>
          <li>*Gender</li>
          <li>LineName</li>
          <li>SubLineName</li>
          <li>ManufacturerName</li>
          <li>BrandName</li>
        </ol>

        <p>Fields marked with * are used for classification.</p>
      </div> */}
    </div>
  );
}