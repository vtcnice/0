#!/usr/bin/env python3
"""
Backend API Testing for VTC Application
Tests all endpoints for company settings, devis creation, and management
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://9281bdbd-340d-47e5-8656-cc72da56b482.preview.emergentagent.com/api"

class VTCAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.created_devis_ids = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        })
    
    def test_company_settings_creation(self):
        """Test POST /api/company-settings with configurable tarifs"""
        print("\n=== Testing Company Settings Creation with Configurable Tarifs ===")
        
        company_data = {
            "nom_societe": "VTC Test Tarifs",
            "numero_siret": "12345678901234",
            "adresse": "123 Avenue des Champs-Élysées, 75008 Paris",
            "telephone": "01 23 45 67 89",
            "email": "contact@vtctest.com",
            "tarif_transfert_km": 2.5,
            "tarif_mise_disposition_h": 90.0
        }
        
        try:
            response = self.session.post(f"{self.base_url}/company-settings", json=company_data)
            
            if response.status_code == 200:
                data = response.json()
                # Verify all fields are present including new tarif fields
                required_fields = ["id", "nom_societe", "numero_siret", "adresse", "telephone", "email", 
                                 "tarif_transfert_km", "tarif_mise_disposition_h", "created_at"]
                missing_fields = [field for field in required_fields if field not in data]
                
                # Verify tarif values are correctly saved
                tarifs_correct = (
                    data.get("tarif_transfert_km") == 2.5 and
                    data.get("tarif_mise_disposition_h") == 90.0
                )
                
                if not missing_fields and tarifs_correct:
                    self.log_test("Company Settings Creation", True, 
                                f"Company settings created with custom tarifs: {data.get('tarif_transfert_km')}€/km, {data.get('tarif_mise_disposition_h')}€/h")
                    return data
                elif missing_fields:
                    self.log_test("Company Settings Creation", False, f"Missing fields in response: {missing_fields}")
                else:
                    self.log_test("Company Settings Creation", False, 
                                f"Incorrect tarif values. Expected: 2.5€/km, 90€/h. Got: {data.get('tarif_transfert_km')}€/km, {data.get('tarif_mise_disposition_h')}€/h")
            else:
                self.log_test("Company Settings Creation", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Company Settings Creation", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_company_settings_retrieval(self):
        """Test GET /api/company-settings"""
        print("\n=== Testing Company Settings Retrieval ===")
        
        try:
            response = self.session.get(f"{self.base_url}/company-settings")
            
            if response.status_code == 200:
                data = response.json()
                expected_tarifs = (
                    data.get("tarif_transfert_km") == 2.5 and
                    data.get("tarif_mise_disposition_h") == 90.0 and
                    data.get("nom_societe") == "VTC Test Tarifs"
                )
                if expected_tarifs:
                    self.log_test("Company Settings Retrieval", True, 
                                f"Company settings retrieved with correct tarifs: {data.get('tarif_transfert_km')}€/km, {data.get('tarif_mise_disposition_h')}€/h")
                    return data
                else:
                    self.log_test("Company Settings Retrieval", False, "Retrieved data doesn't match expected values or tarifs")
            else:
                self.log_test("Company Settings Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Company Settings Retrieval", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_devis_creation_transfert(self):
        """Test POST /api/devis for transfert type with configurable tarifs"""
        print("\n=== Testing Devis Creation - Transfert with Custom Tarifs ===")
        
        devis_data = {
            "client": {
                "nom": "Test",
                "prenom": "User",
                "adresse": "Test Address",
                "telephone": "0123456789",
                "email": "test@test.com"
            },
            "type_prestation": "transfert",
            "adresse_prise_en_charge": "Point A",
            "adresse_destination": "Point B",
            "nombre_kilometres": 40
        }
        
        try:
            response = self.session.post(f"{self.base_url}/devis", json=devis_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify calculations for transfert with custom tarif (2.5€/km, 10% TVA)
                expected_prix_ht = 40 * 2.5  # 100€
                expected_tva = expected_prix_ht * 0.10  # 10€
                expected_ttc = expected_prix_ht + expected_tva  # 110€
                
                calculations_correct = (
                    data.get("prix_unitaire") == 2.5 and
                    data.get("prix_ht") == expected_prix_ht and
                    data.get("taux_tva") == 0.10 and
                    abs(data.get("montant_tva", 0) - expected_tva) < 0.01 and
                    abs(data.get("prix_ttc", 0) - expected_ttc) < 0.01
                )
                
                if calculations_correct:
                    self.log_test("Devis Creation Transfert", True, 
                                f"Devis created with custom tarif calculations: 40km × 2.5€ = {expected_prix_ht}€ HT + {expected_tva}€ TVA = {expected_ttc}€ TTC")
                    self.created_devis_ids.append(data.get("id"))
                    return data
                else:
                    self.log_test("Devis Creation Transfert", False, 
                                f"Incorrect calculations. Expected: {expected_ttc}€ TTC (with 2.5€/km tarif), Got: {data.get('prix_ttc')}€ TTC")
            else:
                self.log_test("Devis Creation Transfert", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Devis Creation Transfert", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_devis_creation_mise_a_disposition(self):
        """Test POST /api/devis for mise_a_disposition type with configurable tarifs"""
        print("\n=== Testing Devis Creation - Mise à Disposition with Custom Tarifs ===")
        
        devis_data = {
            "client": {
                "nom": "Test",
                "prenom": "User2",
                "adresse": "Test Address",
                "telephone": "0123456789",
                "email": "test2@test.com"
            },
            "type_prestation": "mise_a_disposition",
            "nombre_heures": 2
        }
        
        try:
            response = self.session.post(f"{self.base_url}/devis", json=devis_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify calculations for mise_a_disposition with custom tarif (90€/h, 20% TVA)
                expected_prix_ht = 2 * 90.0  # 180€
                expected_tva = expected_prix_ht * 0.20  # 36€
                expected_ttc = expected_prix_ht + expected_tva  # 216€
                
                calculations_correct = (
                    data.get("prix_unitaire") == 90.0 and
                    data.get("prix_ht") == expected_prix_ht and
                    data.get("taux_tva") == 0.20 and
                    abs(data.get("montant_tva", 0) - expected_tva) < 0.01 and
                    abs(data.get("prix_ttc", 0) - expected_ttc) < 0.01
                )
                
                if calculations_correct:
                    self.log_test("Devis Creation Mise à Disposition", True, 
                                f"Devis created with custom tarif calculations: 2h × 90€ = {expected_prix_ht}€ HT + {expected_tva}€ TVA = {expected_ttc}€ TTC")
                    self.created_devis_ids.append(data.get("id"))
                    return data
                else:
                    self.log_test("Devis Creation Mise à Disposition", False, 
                                f"Incorrect calculations. Expected: {expected_ttc}€ TTC (with 90€/h tarif), Got: {data.get('prix_ttc')}€ TTC")
            else:
                self.log_test("Devis Creation Mise à Disposition", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Devis Creation Mise à Disposition", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_devis_validation(self):
        """Test validation for devis creation"""
        print("\n=== Testing Devis Validation ===")
        
        # Test missing kilometres for transfert
        invalid_transfert = {
            "client": {
                "nom": "Test",
                "prenom": "User",
                "adresse": "Test Address",
                "telephone": "0123456789",
                "email": "test@test.com"
            },
            "type_prestation": "transfert",
            "adresse_prise_en_charge": "Point A",
            "adresse_destination": "Point B"
            # Missing nombre_kilometres
        }
        
        try:
            response = self.session.post(f"{self.base_url}/devis", json=invalid_transfert)
            if response.status_code == 400:
                self.log_test("Devis Validation - Missing KM", True, "Correctly rejected transfert without kilometres")
            else:
                self.log_test("Devis Validation - Missing KM", False, f"Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Devis Validation - Missing KM", False, f"Request failed: {str(e)}")
        
        # Test missing hours for mise_a_disposition
        invalid_disposition = {
            "client": {
                "nom": "Test",
                "prenom": "User",
                "adresse": "Test Address",
                "telephone": "0123456789",
                "email": "test@test.com"
            },
            "type_prestation": "mise_a_disposition"
            # Missing nombre_heures
        }
        
        try:
            response = self.session.post(f"{self.base_url}/devis", json=invalid_disposition)
            if response.status_code == 400:
                self.log_test("Devis Validation - Missing Hours", True, "Correctly rejected mise_a_disposition without hours")
            else:
                self.log_test("Devis Validation - Missing Hours", False, f"Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Devis Validation - Missing Hours", False, f"Request failed: {str(e)}")
    
    def test_devis_without_company_settings(self):
        """Test devis creation without company settings configured"""
        print("\n=== Testing Devis Creation Without Company Settings ===")
        
        # First, clear any existing company settings by creating a fresh test
        # This test should be run before company settings are created
        devis_data = {
            "client": {
                "nom": "Test",
                "prenom": "User",
                "adresse": "Test Address",
                "telephone": "0123456789",
                "email": "test@test.com"
            },
            "type_prestation": "transfert",
            "adresse_prise_en_charge": "Point A",
            "adresse_destination": "Point B",
            "nombre_kilometres": 40
        }
        
        try:
            response = self.session.post(f"{self.base_url}/devis", json=devis_data)
            if response.status_code == 400:
                error_message = response.json().get("detail", "")
                if "Paramètres de société non configurés" in error_message:
                    self.log_test("Devis Without Company Settings", True, "Correctly rejected devis creation without company settings")
                else:
                    self.log_test("Devis Without Company Settings", False, f"Wrong error message: {error_message}")
            else:
                self.log_test("Devis Without Company Settings", False, f"Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Devis Without Company Settings", False, f"Request failed: {str(e)}")
    
    def test_devis_list(self):
        """Test GET /api/devis"""
        print("\n=== Testing Devis List ===")
        
        try:
            response = self.session.get(f"{self.base_url}/devis")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) >= len(self.created_devis_ids):
                    self.log_test("Devis List", True, f"Retrieved {len(data)} devis successfully")
                    return data
                else:
                    self.log_test("Devis List", False, f"Expected at least {len(self.created_devis_ids)} devis, got {len(data) if isinstance(data, list) else 'invalid response'}")
            else:
                self.log_test("Devis List", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Devis List", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_devis_retrieval(self):
        """Test GET /api/devis/{devis_id}"""
        print("\n=== Testing Single Devis Retrieval ===")
        
        if not self.created_devis_ids:
            self.log_test("Single Devis Retrieval", False, "No devis IDs available for testing")
            return None
        
        devis_id = self.created_devis_ids[0]
        
        try:
            response = self.session.get(f"{self.base_url}/devis/{devis_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == devis_id:
                    self.log_test("Single Devis Retrieval", True, f"Retrieved devis {devis_id} successfully")
                    return data
                else:
                    self.log_test("Single Devis Retrieval", False, "Retrieved devis ID doesn't match requested ID")
            else:
                self.log_test("Single Devis Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Single Devis Retrieval", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_devis_to_facture_conversion(self):
        """Test PUT /api/devis/{devis_id}/convert-to-facture"""
        print("\n=== Testing Devis to Facture Conversion ===")
        
        if not self.created_devis_ids:
            self.log_test("Devis to Facture Conversion", False, "No devis IDs available for testing")
            return None
        
        devis_id = self.created_devis_ids[0]
        
        try:
            response = self.session.put(f"{self.base_url}/devis/{devis_id}/convert-to-facture")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("is_facture") == True:
                    self.log_test("Devis to Facture Conversion", True, f"Successfully converted devis {devis_id} to facture")
                    return data
                else:
                    self.log_test("Devis to Facture Conversion", False, "Devis not marked as facture after conversion")
            else:
                self.log_test("Devis to Facture Conversion", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Devis to Facture Conversion", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_factures_list(self):
        """Test GET /api/factures"""
        print("\n=== Testing Factures List ===")
        
        try:
            response = self.session.get(f"{self.base_url}/factures")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    factures_count = len(data)
                    # Verify all returned items are factures
                    all_factures = all(item.get("is_facture") == True for item in data)
                    
                    if all_factures:
                        self.log_test("Factures List", True, f"Retrieved {factures_count} factures successfully")
                        return data
                    else:
                        self.log_test("Factures List", False, "Some items in factures list are not marked as factures")
                else:
                    self.log_test("Factures List", False, "Response is not a list")
            else:
                self.log_test("Factures List", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Factures List", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_invalid_devis_retrieval(self):
        """Test GET /api/devis/{invalid_id}"""
        print("\n=== Testing Invalid Devis Retrieval ===")
        
        invalid_id = "non-existent-id"
        
        try:
            response = self.session.get(f"{self.base_url}/devis/{invalid_id}")
            
            if response.status_code == 404:
                self.log_test("Invalid Devis Retrieval", True, "Correctly returned 404 for non-existent devis")
            else:
                self.log_test("Invalid Devis Retrieval", False, f"Expected 404, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Invalid Devis Retrieval", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"🚀 Starting VTC Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test company settings
        self.test_company_settings_creation()
        self.test_company_settings_retrieval()
        
        # Test devis creation and calculations
        self.test_devis_creation_transfert()
        self.test_devis_creation_mise_a_disposition()
        
        # Test validation
        self.test_devis_validation()
        
        # Test devis management
        self.test_devis_list()
        self.test_devis_retrieval()
        
        # Test conversion and factures
        self.test_devis_to_facture_conversion()
        self.test_factures_list()
        
        # Test error handling
        self.test_invalid_devis_retrieval()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if total - passed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   ❌ {result['test']}: {result['message']}")
        
        print(f"\n🎯 Overall Success Rate: {(passed/total)*100:.1f}%")
        
        return passed == total

if __name__ == "__main__":
    tester = VTCAPITester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)