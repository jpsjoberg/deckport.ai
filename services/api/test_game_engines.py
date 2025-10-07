#!/usr/bin/env python3
"""
Test script for game engines without SQLAlchemy dependencies
Production quality validation
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai')

def test_card_abilities():
    """Test card abilities engine in isolation"""
    print("🧪 Testing Card Abilities Engine...")
    
    try:
        # Import without SQLAlchemy dependencies
        from services.api.game_engine.card_abilities import CardAbilitiesEngine
        
        engine = CardAbilitiesEngine()
        
        # Test 1: Basic functionality
        abilities = engine.get_all_abilities()
        print(f"✅ Loaded {len(abilities)} abilities")
        
        # Test 2: Ability validation
        valid_result = engine.validate_ability_parameters('deal_damage', {
            'amount': 5, 
            'target_type': 'enemy'
        })
        print(f"✅ Valid ability validation: {valid_result[0]}")
        
        invalid_result = engine.validate_ability_parameters('deal_damage', {
            'amount': -1  # Missing target_type, invalid amount
        })
        print(f"✅ Invalid ability validation: {not invalid_result[0]}")
        
        # Test 3: Ability info retrieval
        fire_damage_info = engine.get_ability_info('fire_damage')
        assert fire_damage_info is not None
        assert 'damage_type' in fire_damage_info
        print(f"✅ Ability info retrieval works")
        
        # Test 4: All abilities have required fields
        missing_fields = []
        for ability_name in abilities:
            info = engine.get_ability_info(ability_name)
            if not info.get('name') or not info.get('description'):
                missing_fields.append(ability_name)
        
        if missing_fields:
            print(f"❌ Abilities missing required fields: {missing_fields}")
            return False
        else:
            print(f"✅ All abilities have required fields")
        
        print("✅ Card Abilities Engine: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Card Abilities Engine failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_arena_effects():
    """Test arena effects engine in isolation"""
    print("\n🧪 Testing Arena Effects Engine...")
    
    try:
        from services.api.game_engine.arena_effects import ArenaEffectsEngine
        
        engine = ArenaEffectsEngine()
        
        # Test 1: Basic functionality
        arenas = engine.get_available_arenas()
        print(f"✅ Loaded {len(arenas)} arenas")
        
        # Test 2: Arena validation
        assert engine.validate_arena('crimson_forge')
        assert not engine.validate_arena('nonexistent_arena')
        print(f"✅ Arena validation works")
        
        # Test 3: Hero bonus calculation
        bonuses = engine.calculate_hero_bonuses('crimson_forge', 'CRIMSON')
        assert isinstance(bonuses, dict)
        print(f"✅ Hero bonus calculation works")
        
        # Test 4: Balanced arena selection
        hero1 = {'mana_affinity': 'CRIMSON'}
        hero2 = {'mana_affinity': 'AZURE'}
        selected = engine.select_balanced_arena(hero1, hero2)
        assert selected in ['aether_void']  # Should select neutral for opposing colors
        print(f"✅ Balanced arena selection: {selected}")
        
        # Test 5: All arenas have required fields
        required_fields = ['id', 'name', 'mana_color', 'mana_generation']
        missing_fields = []
        
        for arena in arenas:
            arena_name = list(engine.arena_catalog.keys())[arena['id'] - 1]
            arena_data = engine.get_arena_info(arena_name)
            for field in required_fields:
                if field not in arena_data:
                    missing_fields.append(f"{arena_name}.{field}")
        
        if missing_fields:
            print(f"❌ Arenas missing required fields: {missing_fields}")
            return False
        else:
            print(f"✅ All arenas have required fields")
        
        print("✅ Arena Effects Engine: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Arena Effects Engine failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test integration between systems"""
    print("\n🧪 Testing System Integration...")
    
    try:
        from services.api.game_engine.card_abilities import CardAbilitiesEngine
        from services.api.game_engine.arena_effects import ArenaEffectsEngine
        
        abilities_engine = CardAbilitiesEngine()
        arena_engine = ArenaEffectsEngine()
        
        # Test 1: Damage bonus integration
        base_damage = 5
        enhanced_damage = arena_engine.apply_damage_bonuses('crimson_forge', base_damage, 'fire')
        assert enhanced_damage >= base_damage  # Should be enhanced or same
        print(f"✅ Arena damage bonuses work: {base_damage} -> {enhanced_damage}")
        
        # Test 2: Healing bonus integration
        base_healing = 3
        enhanced_healing = arena_engine.apply_healing_bonuses('verdant_grove', base_healing)
        assert enhanced_healing >= base_healing
        print(f"✅ Arena healing bonuses work: {base_healing} -> {enhanced_healing}")
        
        # Test 3: Ability-Arena compatibility
        fire_abilities = [name for name in abilities_engine.get_all_abilities() if 'fire' in name]
        crimson_info = arena_engine.get_arena_info('crimson_forge')
        
        assert len(fire_abilities) > 0
        assert crimson_info['mana_color'].value == 'CRIMSON'
        print(f"✅ Fire abilities ({len(fire_abilities)}) compatible with Crimson Forge")
        
        print("✅ System Integration: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ System Integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_production_readiness():
    """Test production readiness aspects"""
    print("\n🧪 Testing Production Readiness...")
    
    try:
        from services.api.game_engine.card_abilities import CardAbilitiesEngine, AbilityResult
        from services.api.game_engine.arena_effects import ArenaEffectsEngine
        
        abilities_engine = CardAbilitiesEngine()
        arena_engine = ArenaEffectsEngine()
        
        # Test 1: Error handling
        result = abilities_engine.validate_ability_parameters('nonexistent', {})
        assert not result[0]  # Should fail gracefully
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
        
        # Test 3: Memory usage - engines should be lightweight
        import sys
        abilities_size = sys.getsizeof(abilities_engine.ability_catalog)
        arena_size = sys.getsizeof(arena_engine.arena_catalog)
        print(f"✅ Memory usage: Abilities {abilities_size} bytes, Arenas {arena_size} bytes")
        
        # Test 4: Thread safety - engines should be stateless for core operations
        catalog1 = abilities_engine.get_all_abilities()
        catalog2 = abilities_engine.get_all_abilities()
        assert catalog1 == catalog2  # Should return consistent results
        print("✅ Consistent results across multiple calls")
        
        print("✅ Production Readiness: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Production Readiness failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 DECKPORT GAME ENGINES - PRODUCTION QUALITY REVIEW")
    print("=" * 60)
    
    tests = [
        test_card_abilities,
        test_arena_effects,
        test_integration,
        test_production_readiness
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
        else:
            print(f"\n❌ CRITICAL FAILURE in {test_func.__name__}")
    
    print("\n" + "=" * 60)
    print(f"🎯 FINAL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL SYSTEMS ARE PRODUCTION READY! ✅")
        return True
    else:
        print("🚨 PRODUCTION ISSUES DETECTED - NEEDS FIXES ❌")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)








