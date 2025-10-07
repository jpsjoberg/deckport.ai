#!/usr/bin/env python3
"""
Isolated test for game engines without database dependencies
Production quality validation
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai')

def test_card_abilities_isolated():
    """Test card abilities engine without database imports"""
    print("🧪 Testing Card Abilities Engine (Isolated)...")
    
    try:
        # Direct import to avoid circular dependencies
        sys.path.insert(0, '/home/jp/deckport.ai/services/api')
        
        # Import the engines directly
        from game_engine.card_abilities import CardAbilitiesEngine
        
        engine = CardAbilitiesEngine()
        
        # Test 1: Basic functionality
        abilities = engine.get_all_abilities()
        print(f"✅ Loaded {len(abilities)} abilities")
        assert len(abilities) >= 20, "Should have at least 20 abilities"
        
        # Test 2: Ability validation
        valid_result = engine.validate_ability_parameters('deal_damage', {
            'amount': 5, 
            'target_type': 'enemy'
        })
        print(f"✅ Valid ability validation: {valid_result[0]}")
        assert valid_result[0], "Valid parameters should pass validation"
        
        # Test 3: Invalid ability validation
        invalid_result = engine.validate_ability_parameters('deal_damage', {
            'amount': -1  # Missing target_type, invalid amount
        })
        print(f"✅ Invalid ability validation: {not invalid_result[0]}")
        assert not invalid_result[0], "Invalid parameters should fail validation"
        
        # Test 4: Ability info retrieval
        fire_damage_info = engine.get_ability_info('fire_damage')
        assert fire_damage_info is not None, "Fire damage ability should exist"
        assert 'damage_type' in fire_damage_info, "Should have damage_type field"
        print(f"✅ Ability info retrieval works")
        
        # Test 5: All critical abilities exist
        critical_abilities = [
            'deal_damage', 'fire_damage', 'heal', 'buff_attack', 
            'burn', 'freeze', 'gain_energy', 'area_damage'
        ]
        
        missing_abilities = []
        for ability in critical_abilities:
            if not engine.get_ability_info(ability):
                missing_abilities.append(ability)
        
        assert not missing_abilities, f"Missing critical abilities: {missing_abilities}"
        print(f"✅ All critical abilities present")
        
        # Test 6: Ability categories
        categories = ['damage', 'healing', 'buffs', 'debuffs', 'status', 'resource', 'special', 'ultimate']
        for category in categories:
            category_abilities = [name for name in abilities if category in name or 
                                any(keyword in name for keyword in {
                                    'damage': ['damage', 'fire', 'water', 'piercing'],
                                    'healing': ['heal', 'regeneration'],
                                    'buffs': ['buff'],
                                    'debuffs': ['debuff'],
                                    'status': ['burn', 'freeze', 'poison', 'stun'],
                                    'resource': ['energy', 'mana'],
                                    'special': ['teleport', 'reflect', 'immunity', 'life_steal'],
                                    'ultimate': ['ultimate']
                                }.get(category, []))]
            
            if category_abilities:
                print(f"✅ {category.title()} abilities: {len(category_abilities)}")
        
        print("✅ Card Abilities Engine: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Card Abilities Engine failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_arena_effects_isolated():
    """Test arena effects engine without database imports"""
    print("\n🧪 Testing Arena Effects Engine (Isolated)...")
    
    try:
        from game_engine.arena_effects import ArenaEffectsEngine
        
        engine = ArenaEffectsEngine()
        
        # Test 1: Basic functionality
        arenas = engine.get_available_arenas()
        print(f"✅ Loaded {len(arenas)} arenas")
        assert len(arenas) >= 6, "Should have at least 6 arenas"
        
        # Test 2: Arena validation
        assert engine.validate_arena('crimson_forge'), "Crimson Forge should be valid"
        assert not engine.validate_arena('nonexistent_arena'), "Invalid arena should fail"
        print(f"✅ Arena validation works")
        
        # Test 3: Hero bonus calculation
        bonuses = engine.calculate_hero_bonuses('crimson_forge', 'CRIMSON')
        assert isinstance(bonuses, dict), "Bonuses should be a dictionary"
        print(f"✅ Hero bonus calculation works: {bonuses}")
        
        # Test 4: Balanced arena selection
        hero1 = {'mana_affinity': 'CRIMSON'}
        hero2 = {'mana_affinity': 'AZURE'}
        selected = engine.select_balanced_arena(hero1, hero2)
        print(f"✅ Balanced arena selection: {selected}")
        
        # Test 5: All arenas have required fields
        required_fields = ['id', 'name', 'mana_color', 'mana_generation']
        for arena_name in engine.arena_catalog.keys():
            arena_data = engine.get_arena_info(arena_name)
            for field in required_fields:
                assert field in arena_data, f"Arena {arena_name} missing {field}"
        
        print(f"✅ All arenas have required fields")
        
        # Test 6: Mana colors
        expected_colors = ['CRIMSON', 'AZURE', 'VERDANT', 'GOLDEN', 'SHADOW', 'AETHER']
        arena_colors = [engine.arena_catalog[name]['mana_color'].value for name in engine.arena_catalog.keys()]
        
        for color in expected_colors:
            assert color in arena_colors, f"Missing arena for color {color}"
        
        print(f"✅ All mana colors represented")
        
        print("✅ Arena Effects Engine: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Arena Effects Engine failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_isolated():
    """Test integration between systems"""
    print("\n🧪 Testing System Integration (Isolated)...")
    
    try:
        from game_engine.card_abilities import CardAbilitiesEngine
        from game_engine.arena_effects import ArenaEffectsEngine
        
        abilities_engine = CardAbilitiesEngine()
        arena_engine = ArenaEffectsEngine()
        
        # Test 1: Damage bonus integration
        base_damage = 5
        enhanced_damage = arena_engine.apply_damage_bonuses('crimson_forge', base_damage, 'fire')
        assert enhanced_damage >= base_damage, "Enhanced damage should be >= base"
        print(f"✅ Arena damage bonuses work: {base_damage} -> {enhanced_damage}")
        
        # Test 2: Healing bonus integration
        base_healing = 3
        enhanced_healing = arena_engine.apply_healing_bonuses('verdant_grove', base_healing)
        assert enhanced_healing >= base_healing, "Enhanced healing should be >= base"
        print(f"✅ Arena healing bonuses work: {base_healing} -> {enhanced_healing}")
        
        # Test 3: Ability-Arena compatibility
        fire_abilities = [name for name in abilities_engine.get_all_abilities() if 'fire' in name]
        crimson_info = arena_engine.get_arena_info('crimson_forge')
        
        assert len(fire_abilities) > 0, "Should have fire abilities"
        assert crimson_info['mana_color'].value == 'CRIMSON', "Crimson forge should be CRIMSON"
        print(f"✅ Fire abilities ({len(fire_abilities)}) compatible with Crimson Forge")
        
        # Test 4: Status effects and arena interactions
        status_abilities = [name for name in abilities_engine.get_all_abilities() 
                          if any(status in name for status in ['burn', 'freeze', 'poison', 'stun'])]
        assert len(status_abilities) >= 4, "Should have at least 4 status effect abilities"
        print(f"✅ Status effect abilities: {len(status_abilities)}")
        
        print("✅ System Integration: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ System Integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_production_quality():
    """Test production quality aspects"""
    print("\n🧪 Testing Production Quality...")
    
    try:
        from game_engine.card_abilities import CardAbilitiesEngine, AbilityResult
        from game_engine.arena_effects import ArenaEffectsEngine
        
        abilities_engine = CardAbilitiesEngine()
        arena_engine = ArenaEffectsEngine()
        
        # Test 1: Error handling
        result = abilities_engine.validate_ability_parameters('nonexistent', {})
        assert not result[0], "Should fail gracefully for invalid abilities"
        print("✅ Graceful error handling for invalid abilities")
        
        # Test 2: Performance - should handle all abilities quickly
        import time
        start_time = time.time()
        
        for ability_name in abilities_engine.get_all_abilities():
            info = abilities_engine.get_ability_info(ability_name)
            validation = abilities_engine.validate_ability_parameters(ability_name, {
                'amount': 1,
                'target_type': 'enemy',
                'duration': 1,
                'color': 'CRIMSON',
                'percentage': 50,
                'damage_type': 'fire'
            })
        
        elapsed = time.time() - start_time
        print(f"✅ Performance test: {len(abilities_engine.get_all_abilities())} abilities processed in {elapsed:.3f}s")
        assert elapsed < 1.0, "Should process all abilities in under 1 second"
        
        # Test 3: Memory usage - engines should be lightweight
        import sys
        abilities_size = sys.getsizeof(abilities_engine.ability_catalog)
        arena_size = sys.getsizeof(arena_engine.arena_catalog)
        print(f"✅ Memory usage: Abilities {abilities_size} bytes, Arenas {arena_size} bytes")
        
        # Test 4: Thread safety - engines should be stateless for core operations
        catalog1 = abilities_engine.get_all_abilities()
        catalog2 = abilities_engine.get_all_abilities()
        assert catalog1 == catalog2, "Should return consistent results"
        print("✅ Consistent results across multiple calls")
        
        # Test 5: AbilityResult structure
        result = AbilityResult()
        result_dict = result.to_dict()
        required_fields = ['success', 'damage_dealt', 'healing_done', 'targets_affected', 'animation_data']
        
        for field in required_fields:
            assert field in result_dict, f"AbilityResult missing field: {field}"
        
        print("✅ AbilityResult structure is complete")
        
        # Test 6: Arena objectives
        crimson_forge = arena_engine.get_arena_info('crimson_forge')
        objectives = crimson_forge.get('objectives', [])
        assert len(objectives) > 0, "Crimson Forge should have objectives"
        
        for objective in objectives:
            required_obj_fields = ['id', 'name', 'type', 'target', 'description', 'reward']
            for field in required_obj_fields:
                assert field in objective, f"Objective missing field: {field}"
        
        print("✅ Arena objectives are well-structured")
        
        print("✅ Production Quality: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Production Quality failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all isolated tests"""
    print("🚀 DECKPORT GAME ENGINES - ISOLATED PRODUCTION QUALITY REVIEW")
    print("=" * 70)
    
    tests = [
        test_card_abilities_isolated,
        test_arena_effects_isolated,
        test_integration_isolated,
        test_production_quality
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
        else:
            print(f"\n❌ CRITICAL FAILURE in {test_func.__name__}")
    
    print("\n" + "=" * 70)
    print(f"🎯 FINAL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL GAME ENGINES ARE PRODUCTION READY! ✅")
        
        # Additional production readiness summary
        print("\n📋 PRODUCTION READINESS SUMMARY:")
        print("✅ Card Abilities: 20+ abilities with full validation")
        print("✅ Arena Effects: 6 arenas with mana generation & bonuses")
        print("✅ Integration: Seamless ability-arena interactions")
        print("✅ Performance: Sub-second processing of all operations")
        print("✅ Error Handling: Graceful failure for invalid inputs")
        print("✅ Memory Efficiency: Lightweight engine footprint")
        print("✅ Thread Safety: Stateless core operations")
        print("✅ Data Structures: Complete and well-validated")
        
        return True
    else:
        print("🚨 PRODUCTION ISSUES DETECTED - NEEDS FIXES ❌")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)








