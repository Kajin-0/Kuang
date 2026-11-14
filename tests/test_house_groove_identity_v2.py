"""Guard that groove identity changes are musical, bounded, and opt-in."""
import unittest
from kuang.house_template import _bass_groove_identity,template
from kuang.house_sources import prepare_kit
from kuang.song import rules_plan
from kuang.schema import ValidationError,dumps,validate


class HouseGrooveIdentityTests(unittest.TestCase):
    def test_distinct_profiles_different_motifs_and_repeatable(self):
        profiles=('straight','deep','jackin','minimal')
        motifs={}
        for p in profiles:
            patterns=[_bass_groove_identity(p,67,bar) for bar in range(16)]
            self.assertEqual(patterns,[_bass_groove_identity(p,67,bar) for bar in range(16)])
            self.assertGreaterEqual(len(set(patterns)),2)
            for pat in patterns:
                self.assertTrue(2<=len(pat)<=4)
                steps=[s for s,_,_ in pat]
                self.assertEqual(steps,sorted(set(steps)))
                self.assertTrue(all(0<=s<=15 and 1<=duration<=3 and degree in (0,4,7)
                                    for s,duration,degree in pat))
            motifs[p]=tuple(patterns)
        self.assertEqual(len(set(motifs.values())),4)

    def test_preserve_legacy_and_retain_chords_drums_fx(self):
        for profile,key,seed in (('deep','E major',67),('jackin','Bb major',83),
                                 ('minimal','F# minor',29),('straight','A minor',41)):
            with self.subTest(profile=profile):
                s,_=rules_plan(f'{profile} house in {key}, 16 bars',seed)
                legacy,lr=template(s,profile=profile,impact_pocket=True)
                explicit_off,_=template(s,profile=profile,impact_pocket=True,groove_identity_v2=False)
                self.assertEqual(dumps(legacy),dumps(explicit_off))
                variant,e=template(s,profile=profile,impact_pocket=True,groove_identity_v2=True)
                replay,_=template(s,profile=profile,impact_pocket=True,groove_identity_v2=True)
                self.assertEqual(dumps(variant),dumps(replay))
                validate(variant)
                self.assertTrue(e['groove_identity_v2'])
                a={t.id:t for t in legacy.tracks}
                b={t.id:t for t in variant.tracks}
                self.assertEqual(set(a),set(b))
                for role in a:
                    self.assertEqual(a[role].instrument,b[role].instrument)
                    self.assertEqual(a[role].effects,b[role].effects)
                    self.assertEqual(a[role].controls,b[role].controls)
                    if role.startswith('track-') and role not in ('track-bass','track-harmony'):
                        self.assertEqual(a[role].clips,b[role].clips)
                self.assertNotEqual(a['track-bass'].clips,b['track-bass'].clips)

    def test_rejects_incompatible_new_mode(self):
        s,_=rules_plan('deep house in C minor, 16 bars',31)
        with self.assertRaises(ValidationError):
            template(s,profile='deep',impact_pocket=False,groove_identity_v2=True)
        with self.assertRaises(ValidationError):
            template(s,profile='deep',impact_pocket=True,groove_identity_v2='yes')


if __name__=="__main__":
    unittest.main()
