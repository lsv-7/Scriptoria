# Sanity Check and Integration Test Script for CineForge AI
import os
import sys

# Python 3.14 compatibility workaround for protobuf C-extension metaclass changes
sys.modules['google._upb._message'] = None

# Add current workspace directory to Python path to enable backend package imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests():
    print("==================================================")
    print("    CineForge AI Backend Integration Verifier    ")
    print("==================================================")

    # 1. Test Imports
    print("\n1. Testing module imports...")
    try:
        from backend.config import Config
        from backend.services.firebase_service import firebase_service
        from backend.services.gemini_service import gemini_service
        from backend.services.granite_service import granite_service
        from backend.services.export_service import export_service
        from backend.app import create_app
        print("   [SUCCESS] All core modules and packages imported successfully.")
    except Exception as e:
        print(f"   [FAILURE] Module import failed: {e}")
        return False

    # 2. Test Firebase Fallback Mode
    print("\n2. Testing Firebase Service Mode...")
    print(f"   Mock Mode Status: {firebase_service.mock_mode}")
    print(f"   Mock Database Path: {firebase_service.mock_db_path}")
    
    # Write a test project
    test_project = {
        "project_id": "test_verification_id",
        "user_id": "verify_user",
        "project_name": "Project Verification",
        "genre": "Neo-Noir Thriller",
        "target_audience": "Adults 18-35",
        "story_idea": "A detective discovers a simulation within a simulation."
    }
    
    try:
        firebase_service.set_document("projects", "test_verification_id", test_project)
        retrieved = firebase_service.get_document("projects", "test_verification_id")
        if retrieved and retrieved.get("project_name") == "Project Verification":
            print("   [SUCCESS] Database read/write operations verified.")
        else:
            print("   [FAILURE] Failed to retrieve written document.")
            return False
    except Exception as e:
        print(f"   [FAILURE] Database test failed: {e}")
        return False

    # 3. Test AI Generation Services (Fallbacks)
    print("\n3. Testing AI Generation Modules...")
    try:
        analysis = gemini_service.generate_story_analysis(
            test_project["story_idea"], test_project["genre"], test_project["target_audience"]
        )
        print("   - Story Analysis generated successfully.")
        
        screenplay = granite_service.generate_screenplay(
            test_project["story_idea"], test_project["genre"], [{"name": "Vikram"}, {"name": "Anya"}]
        )
        print("   - Screenplay generated successfully.")
        
        scene_script = granite_service.generate_scene_script(
            test_project["story_idea"], test_project["genre"], [{"name": "Vikram"}, {"name": "Anya"}], "Short Film",
            {"scene_number": 1, "location": "INT. APARTMENT - DAY", "characters": "Vikram, Anya", "objective": "Discuss plans", "duration": "3 mins"},
            [{"scene_number": 1, "location": "INT. APARTMENT - DAY", "characters": "Vikram, Anya", "objective": "Discuss plans", "duration": "3 mins"}]
        )
        print("   - Single scene script generated successfully.")
        
        scenes = gemini_service.generate_scenes(test_project["story_idea"], test_project["genre"])
        print("   - Scenes generated successfully.")
        
        storyboards = gemini_service.generate_storyboard(test_project["story_idea"], scenes.get("scenes", []))
        print("   - Storyboard prompts generated successfully.")
        
        sound = granite_service.generate_sound_design(test_project["story_idea"], test_project["genre"])
        print("   - Sound Design generated successfully.")
        
        prod = granite_service.generate_production_plan(test_project["story_idea"], test_project["genre"])
        print("   - Production Plan generated successfully.")
        
        budget = granite_service.generate_budget_plan(test_project["story_idea"], test_project["genre"])
        print("   - Budget Plan generated successfully.")
        
        print("   [SUCCESS] All AI generation triggers completed.")
    except Exception as e:
        print(f"   [FAILURE] AI generation service failed: {e}")
        return False

    # 4. Test Exporter Compile
    print("\n4. Testing Document Exporter Compilations...")
    try:
        compiled_data = {
            "story_analysis": analysis,
            "narrative_structure": gemini_service.generate_narrative_structure(test_project["story_idea"], test_project["genre"]),
            "screenplay": {"screenplay_text": screenplay},
            "characters": gemini_service.generate_characters(test_project["story_idea"], test_project["genre"]),
            "scene_breakdown": scenes,
            "storyboard": storyboards,
            "sound_design": sound,
            "production_plan": prod,
            "budget_plan": budget
        }
        
        # Compile PDF
        pdf_bytes = export_service.generate_pdf(test_project, compiled_data)
        print(f"   - PDF Compiled successfully: {len(pdf_bytes)} bytes.")
        
        # Compile DOCX
        docx_bytes = export_service.generate_docx(test_project, compiled_data)
        print(f"   - DOCX Compiled successfully: {len(docx_bytes)} bytes.")
        
        # Compile TXT
        txt_bytes = export_service.generate_txt(test_project, compiled_data)
        print(f"   - TXT Compiled successfully: {len(txt_bytes)} bytes.")
        
        print("   [SUCCESS] Exporters compiled binary bytes correctly.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"   [FAILURE] Exporters test failed: {e}")
        return False

    print("\n==================================================")
    print("    VERIFICATION COMPLETED: ALL SYSTEM CHECKS PASS ")
    print("==================================================")
    
    # Clean up verification entry
    firebase_service.delete_document("projects", "test_verification_id")
    if os.path.exists(firebase_service.mock_db_path):
        os.remove(firebase_service.mock_db_path)
        
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
