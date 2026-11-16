"""Regression of production source exclusions and non-aesthetic timbre flags."""
import hashlib
import json
import unittest
from pathlib import Path

from kuang import autonomous_palette as palette
from kuang.house_source_policy import (
    VERSION, source_exclusion, bass_timbre_observation, pad_timbre_observation,
)
from kuang.schema import ValidationError
from tests.test_autonomous_palette import FakeRenderer, PaletteTests, preset


class HouseProducerSourcePolicy(unittest.TestCase):
    def test_exact_negative_bass_source_rejected_not_a_broad_name_block(self):
        sha="6e4e2259440015123c1f5670b2991674638c00f0ed198119dd20f3fb97cd918c"
        self.assertEqual(source_exclusion('bass',sha),
                         'producer_rejected_growling_minimal_house_bass')
        self.assertIsNone(source_exclusion('chord',sha))
        self.assertIsNone(source_exclusion('bass','f'*64))
        for invalid in ('broken',None,123,'G'*64):
            with self.assertRaises(ValidationError):
                source_exclusion('bass',invalid)

    def test_timbre_observation_is_a_review_not_a_growl_or_quality_classifier(self):
        ld={'low_fraction':.8426,'mid_fraction':.1552,
            'high_fraction':.0022,'stereo_side_fraction':.6953,
            'attack_ratio':1.78,'tail_ratio':.09}
        observed=bass_timbre_observation(ld)
        self.assertEqual(observed['version'],VERSION)
        self.assertTrue(observed['low_dominant_wide_source_review'])
        self.assertIsNone(observed['growl_detected'])
        self.assertEqual(observed['musical_quality'],'UNKNOWN')
        good=dict(ld,stereo_side_fraction=0.)
        self.assertFalse(bass_timbre_observation(good)['low_dominant_wide_source_review'])
        for bad in (dict(ld,low_fraction=float('nan')),dict(ld,mid_fraction='bad')):
            with self.assertRaises(ValidationError):bass_timbre_observation(bad)

    def test_pad_low_band_preflight_uses_native_context_not_quality_claims(self):
        review=pad_timbre_observation({'low_fraction':.2797})
        self.assertTrue(review['low_heavy_pad_review'])
        self.assertEqual(review['required_follow_up'],'NATIVE_PAD_BASS_MASKING_REVIEW')
        self.assertIsNone(review['growl_detected'])
        self.assertEqual(review['musical_quality'],'UNKNOWN')
        self.assertFalse(pad_timbre_observation({'low_fraction':.0013})['low_heavy_pad_review'])
        for f in ({}, {'low_fraction':float('nan')}, {'low_fraction':2.}):
            with self.assertRaises(ValidationError): pad_timbre_observation(f)

    def test_selector_does_not_audition_rejected_catalog_hash(self):
        fixture=PaletteTests(methodName='test_determinism_and_private_output')
        fixture.setUp()
        try:
            item=next(r for r in fixture.rows if r['preset_style']=='Bass')
            name='LD Bass'
            raw=json.dumps(preset(name)).encode()
            actual=hashlib.sha256(raw).hexdigest()
            # The catalog-level source hash must match a rejected byte identity
            # to exercise the selector, independent of human-readable names.
            from unittest.mock import patch
            with patch('kuang.autonomous_palette.source_exclusion',
                       side_effect=lambda role,sha: 'producer_rejected_source' if sha == actual and role=='bass' else None):
                file=fixture.presets/item['path'];file.write_bytes(raw)
                item.update(preset_name=name,sha256=actual,size=len(raw))
                # Only one other viable bass source: force the bounded
                # search to inspect (and exclude) the rejected catalog row.
                others=[r for r in fixture.rows if r['preset_style']=='Bass' and r is not item]
                for ignored in others[1:]: ignored['compatibility']='unsupported'
                fixture.write_catalog()
                r,renderer=fixture.run_selection('policy-selection',seed=17,per_role=2,max_candidates=10)
            self.assertEqual(r['status'],'complete')
            selection=json.loads((fixture.root/'policy-selection/selection.json').read_text())
            self.assertNotEqual(selection['roles']['bass']['source_sha256'],actual)
            self.assertTrue(any(x.get('reason','').startswith('producer-source-policy:')
                                for x in json.loads((fixture.root/'policy-selection/decision.json').read_text())['decisions']))
            self.assertNotIn(actual,[h for role,h in renderer.calls if role=='bass'])
        finally:
            fixture.tearDown()


if __name__ == '__main__':
    unittest.main()
