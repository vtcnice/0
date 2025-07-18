import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import jsPDF from "jspdf";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [activeTab, setActiveTab] = useState("devis");
  const [companySettings, setCompanySettings] = useState({
    nom_societe: "",
    numero_siret: "",
    adresse: "",
    telephone: "",
    email: "",
    tarif_transfert_km: 2.0,
    tarif_mise_disposition_h: 80.0
  });
  const [devisData, setDevisData] = useState({
    client: {
      nom: "",
      prenom: "",
      adresse: "",
      telephone: "",
      email: ""
    },
    type_prestation: "transfert",
    adresse_prise_en_charge: "",
    adresse_destination: "",
    nombre_kilometres: "",
    nombre_heures: ""
  });
  const [devisList, setDevisList] = useState([]);
  const [facturesList, setFacturesList] = useState([]);
  const [settingsLoaded, setSettingsLoaded] = useState(false);

  // Charger les paramètres de société
  useEffect(() => {
    loadCompanySettings();
    loadDevis();
    loadFactures();
  }, []);

  const loadCompanySettings = async () => {
    try {
      const response = await axios.get(`${API}/company-settings`);
      setCompanySettings(response.data);
      setSettingsLoaded(true);
    } catch (error) {
      console.log("Paramètres de société non trouvés");
      setSettingsLoaded(true);
    }
  };

  const loadDevis = async () => {
    try {
      const response = await axios.get(`${API}/devis`);
      setDevisList(response.data);
    } catch (error) {
      console.error("Erreur lors du chargement des devis:", error);
    }
  };

  const loadFactures = async () => {
    try {
      const response = await axios.get(`${API}/factures`);
      setFacturesList(response.data);
    } catch (error) {
      console.error("Erreur lors du chargement des factures:", error);
    }
  };

  const saveCompanySettings = async () => {
    try {
      await axios.post(`${API}/company-settings`, companySettings);
      alert("Paramètres de société sauvegardés avec succès !");
    } catch (error) {
      console.error("Erreur lors de la sauvegarde:", error);
      alert("Erreur lors de la sauvegarde des paramètres");
    }
  };

  const createDevis = async () => {
    try {
      const response = await axios.post(`${API}/devis`, devisData);
      alert("Devis créé avec succès !");
      setDevisData({
        client: {
          nom: "",
          prenom: "",
          adresse: "",
          telephone: "",
          email: ""
        },
        type_prestation: "transfert",
        adresse_prise_en_charge: "",
        adresse_destination: "",
        nombre_kilometres: "",
        nombre_heures: ""
      });
      loadDevis();
    } catch (error) {
      console.error("Erreur lors de la création du devis:", error);
      alert("Erreur lors de la création du devis");
    }
  };

  const convertToFacture = async (devisId) => {
    try {
      await axios.put(`${API}/devis/${devisId}/convert-to-facture`);
      alert("Devis converti en facture avec succès !");
      loadDevis();
      loadFactures();
    } catch (error) {
      console.error("Erreur lors de la conversion:", error);
      alert("Erreur lors de la conversion en facture");
    }
  };

  const generatePDF = (document, type) => {
    const doc = new jsPDF();
    
    // En-tête de l'entreprise
    doc.setFontSize(16);
    doc.text(companySettings.nom_societe, 20, 20);
    doc.setFontSize(10);
    doc.text(`SIRET: ${companySettings.numero_siret}`, 20, 30);
    doc.text(companySettings.adresse, 20, 40);
    doc.text(`Tel: ${companySettings.telephone}`, 20, 50);
    doc.text(`Email: ${companySettings.email}`, 20, 60);
    
    // Titre du document
    doc.setFontSize(18);
    doc.text(type === "devis" ? "DEVIS" : "FACTURE", 150, 20);
    
    // Informations du document
    doc.setFontSize(12);
    doc.text(`N°: ${document.numero_devis}`, 150, 35);
    doc.text(`Date: ${new Date(document.date_creation).toLocaleDateString('fr-FR')}`, 150, 45);
    doc.text(`Validité: ${new Date(document.date_validite).toLocaleDateString('fr-FR')}`, 150, 55);
    
    // Informations client
    doc.setFontSize(14);
    doc.text("CLIENT:", 20, 80);
    doc.setFontSize(10);
    doc.text(`${document.client.nom} ${document.client.prenom}`, 20, 90);
    doc.text(document.client.adresse, 20, 100);
    doc.text(`Tel: ${document.client.telephone}`, 20, 110);
    doc.text(`Email: ${document.client.email}`, 20, 120);
    
    // Détails de la prestation
    doc.setFontSize(14);
    doc.text("PRESTATION:", 20, 140);
    doc.setFontSize(10);
    
    let y = 150;
    if (document.type_prestation === "transfert") {
      doc.text(`Type: Transfert`, 20, y);
      doc.text(`De: ${document.adresse_prise_en_charge}`, 20, y + 10);
      doc.text(`À: ${document.adresse_destination}`, 20, y + 20);
      doc.text(`Distance: ${document.nombre_kilometres} km`, 20, y + 30);
      doc.text(`Prix unitaire: 2,00€/km`, 20, y + 40);
      y += 50;
    } else {
      doc.text(`Type: Mise à disposition`, 20, y);
      doc.text(`Durée: ${document.nombre_heures} heures`, 20, y + 10);
      doc.text(`Prix unitaire: 80,00€/h`, 20, y + 20);
      y += 30;
    }
    
    // Calculs
    doc.setFontSize(12);
    doc.text(`Prix HT: ${document.prix_ht.toFixed(2)}€`, 120, y);
    doc.text(`TVA (${(document.taux_tva * 100).toFixed(0)}%): ${document.montant_tva.toFixed(2)}€`, 120, y + 15);
    doc.text(`Prix TTC: ${document.prix_ttc.toFixed(2)}€`, 120, y + 30);
    
    // Sauvegarde du PDF
    doc.save(`${type}_${document.numero_devis}.pdf`);
  };

  const handleCompanySettingsChange = (e) => {
    const { name, value } = e.target;
    setCompanySettings(prev => ({
      ...prev,
      [name]: name.includes('tarif_') ? parseFloat(value) || 0 : value
    }));
  };

  const handleDevisChange = (e) => {
    const { name, value } = e.target;
    if (name.startsWith('client.')) {
      const clientField = name.split('.')[1];
      setDevisData(prev => ({
        ...prev,
        client: {
          ...prev.client,
          [clientField]: value
        }
      }));
    } else {
      setDevisData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  if (!settingsLoaded) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Chargement...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
          Application VTC - Gestion des Devis
        </h1>
        
        {/* Navigation */}
        <div className="flex justify-center mb-8">
          <div className="bg-white rounded-lg shadow-md p-1">
            <button
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                activeTab === "reglages" ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"
              }`}
              onClick={() => setActiveTab("reglages")}
            >
              Réglages
            </button>
            <button
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                activeTab === "devis" ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"
              }`}
              onClick={() => setActiveTab("devis")}
            >
              Nouveau Devis
            </button>
            <button
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                activeTab === "liste" ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"
              }`}
              onClick={() => setActiveTab("liste")}
            >
              Liste des Devis
            </button>
            <button
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                activeTab === "factures" ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"
              }`}
              onClick={() => setActiveTab("factures")}
            >
              Factures
            </button>
          </div>
        </div>

        {/* Contenu des onglets */}
        <div className="max-w-4xl mx-auto">
          {/* Onglet Réglages */}
          {activeTab === "reglages" && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-bold mb-6">Paramètres de Société</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nom de la société
                  </label>
                  <input
                    type="text"
                    name="nom_societe"
                    value={companySettings.nom_societe}
                    onChange={handleCompanySettingsChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ex: Transport VTC Paris"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Numéro SIRET
                  </label>
                  <input
                    type="text"
                    name="numero_siret"
                    value={companySettings.numero_siret}
                    onChange={handleCompanySettingsChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ex: 12345678901234"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Adresse
                  </label>
                  <input
                    type="text"
                    name="adresse"
                    value={companySettings.adresse}
                    onChange={handleCompanySettingsChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ex: 123 Rue de la Paix, 75001 Paris"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Téléphone
                  </label>
                  <input
                    type="text"
                    name="telephone"
                    value={companySettings.telephone}
                    onChange={handleCompanySettingsChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ex: 01 23 45 67 89"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={companySettings.email}
                    onChange={handleCompanySettingsChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ex: contact@votreentreprise.com"
                  />
                </div>
              </div>
              
              {/* Tarifs configurables */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-4 text-gray-800">Tarifs</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Tarif Transfert (€/km)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      name="tarif_transfert_km"
                      value={companySettings.tarif_transfert_km}
                      onChange={handleCompanySettingsChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Ex: 2.00"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Tarif Mise à disposition (€/h)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      name="tarif_mise_disposition_h"
                      value={companySettings.tarif_mise_disposition_h}
                      onChange={handleCompanySettingsChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Ex: 80.00"
                    />
                  </div>
                </div>
              </div>
              <div className="mt-6">
                <button
                  onClick={saveCompanySettings}
                  className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                >
                  Sauvegarder les Paramètres
                </button>
              </div>
            </div>
          )}

          {/* Onglet Nouveau Devis */}
          {activeTab === "devis" && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-bold mb-6">Nouveau Devis</h2>
              
              {/* Type de prestation */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Type de prestation
                </label>
                <div className="flex space-x-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="type_prestation"
                      value="transfert"
                      checked={devisData.type_prestation === "transfert"}
                      onChange={handleDevisChange}
                      className="mr-2"
                    />
                    Transfert ({companySettings.tarif_transfert_km}€/km - TVA 10%)
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="type_prestation"
                      value="mise_a_disposition"
                      checked={devisData.type_prestation === "mise_a_disposition"}
                      onChange={handleDevisChange}
                      className="mr-2"
                    />
                    Mise à disposition ({companySettings.tarif_mise_disposition_h}€/h - TVA 20%)
                  </label>
                </div>
              </div>

              {/* Informations client */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-4">Informations Client</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Nom</label>
                    <input
                      type="text"
                      name="client.nom"
                      value={devisData.client.nom}
                      onChange={handleDevisChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Prénom</label>
                    <input
                      type="text"
                      name="client.prenom"
                      value={devisData.client.prenom}
                      onChange={handleDevisChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Adresse</label>
                    <input
                      type="text"
                      name="client.adresse"
                      value={devisData.client.adresse}
                      onChange={handleDevisChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Téléphone</label>
                    <input
                      type="text"
                      name="client.telephone"
                      value={devisData.client.telephone}
                      onChange={handleDevisChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                    <input
                      type="email"
                      name="client.email"
                      value={devisData.client.email}
                      onChange={handleDevisChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Détails de la prestation */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-4">Détails de la Prestation</h3>
                {devisData.type_prestation === "transfert" ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Adresse de prise en charge
                      </label>
                      <input
                        type="text"
                        name="adresse_prise_en_charge"
                        value={devisData.adresse_prise_en_charge}
                        onChange={handleDevisChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Adresse de destination
                      </label>
                      <input
                        type="text"
                        name="adresse_destination"
                        value={devisData.adresse_destination}
                        onChange={handleDevisChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Nombre de kilomètres
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        name="nombre_kilometres"
                        value={devisData.nombre_kilometres}
                        onChange={handleDevisChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Nombre d'heures
                      </label>
                      <input
                        type="number"
                        step="0.5"
                        name="nombre_heures"
                        value={devisData.nombre_heures}
                        onChange={handleDevisChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-6">
                <button
                  onClick={createDevis}
                  className="w-full bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
                >
                  Créer le Devis
                </button>
              </div>
            </div>
          )}

          {/* Onglet Liste des Devis */}
          {activeTab === "liste" && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-bold mb-6">Liste des Devis</h2>
              {devisList.length === 0 ? (
                <p className="text-gray-500 text-center py-8">Aucun devis trouvé</p>
              ) : (
                <div className="space-y-4">
                  {devisList.map((devis) => (
                    <div key={devis.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-semibold text-lg">{devis.numero_devis}</h3>
                          <p className="text-gray-600">
                            {devis.client.nom} {devis.client.prenom}
                          </p>
                          <p className="text-gray-500 text-sm">
                            {devis.type_prestation === "transfert" ? "Transfert" : "Mise à disposition"}
                          </p>
                          <p className="text-gray-500 text-sm">
                            Date: {new Date(devis.date_creation).toLocaleDateString('fr-FR')}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-green-600">
                            {devis.prix_ttc.toFixed(2)}€ TTC
                          </p>
                          <div className="mt-2 space-y-2">
                            <button
                              onClick={() => generatePDF(devis, "devis")}
                              className="block w-full bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors"
                            >
                              Télécharger PDF
                            </button>
                            {!devis.is_facture && (
                              <button
                                onClick={() => convertToFacture(devis.id)}
                                className="block w-full bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700 transition-colors"
                              >
                                Convertir en Facture
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Onglet Factures */}
          {activeTab === "factures" && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-bold mb-6">Factures</h2>
              {facturesList.length === 0 ? (
                <p className="text-gray-500 text-center py-8">Aucune facture trouvée</p>
              ) : (
                <div className="space-y-4">
                  {facturesList.map((facture) => (
                    <div key={facture.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-semibold text-lg">{facture.numero_devis}</h3>
                          <p className="text-gray-600">
                            {facture.client.nom} {facture.client.prenom}
                          </p>
                          <p className="text-gray-500 text-sm">
                            {facture.type_prestation === "transfert" ? "Transfert" : "Mise à disposition"}
                          </p>
                          <p className="text-gray-500 text-sm">
                            Date: {new Date(facture.date_creation).toLocaleDateString('fr-FR')}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-green-600">
                            {facture.prix_ttc.toFixed(2)}€ TTC
                          </p>
                          <div className="mt-2">
                            <button
                              onClick={() => generatePDF(facture, "facture")}
                              className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors"
                            >
                              Télécharger PDF
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;