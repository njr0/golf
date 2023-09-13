from tdda.referencetest import ReferenceTestCase, tag

from handicapindex import Round

class TestHandicaps(ReferenceTestCase):
    def testStablefordRound(self):
        r = Round('2021-06-27', 22.7, 'Broomieknowe', 'white', stableford=38)
        self.assertEqual(r.differential, round(21.1, 1))

    def testStrokesRound(self):
        r = Round('2021-06-27', 22.7, 'Broomieknowe', 'white', strokes=93,
                  discards=0)
        self.assertEqual(r.differential, round(21.1, 1))

    def testAdjustedStrokesRound(self):
        r = Round('2021-06-27', 22.7, 'Broomieknowe', 'white',
                  adjusted_strokes=93)
        self.assertEqual(r.differential, round(21.1, 1))

    def testMultipleInputsZeroDiscards(self):
        r1 = Round('2021-09-12', 22.3, 'Broomieknowe', 'white', stableford=35,
                   discards=0)
        r2 = Round('2021-09-12', 22.3, 'Broomieknowe', 'white', discards=0,
                  adjusted_strokes=95)
        r3 = Round('2021-09-12', 22.3, 'Broomieknowe', 'white', discards=0,
                  strokes=95)

        self.assertEqual(r1, r2)
        self.assertEqual(r2, r3)
        self.assertEqual(r3, r1)

        self.assertEqual(str(r1), str(r2))
        self.assertEqual(str(r2), str(r3))
        self.assertEqual(str(r3), str(r1))

        self.assertEqual(r1.stableford, 35)
        self.assertEqual(r1.adjusted_strokes, 95)
        self.assertEqual(r1.strokes, 95)
        self.assertEqual(r1.nett_strokes, 71)
        self.assertEqual(r1.discards, 0)
        self.assertAlmostEqual(r1.differential, 22.9)

    def testMultipleInputsWithDiscards(self):
        r1 = Round('2021-09-12', 22.3, 'Broomieknowe', 'white', stableford=35,
                   discards=3)
        r2 = Round('2021-09-12', 22.3, 'Broomieknowe', 'white', discards=3,
                  adjusted_strokes=95)
        r3 = Round('2021-09-12', 22.3, 'Broomieknowe', 'white', discards=3,
                  strokes=98)

        self.assertEqual(r1, r2)
        self.assertEqual(r2, r3)
        self.assertEqual(r3, r1)

        self.assertEqual(str(r1), str(r2))
        self.assertEqual(str(r2), str(r3))
        self.assertEqual(str(r3), str(r1))

        self.assertEqual(r1.stableford, 35)
        self.assertEqual(r1.adjusted_strokes, 95)
        self.assertEqual(r1.strokes, 98)
        self.assertEqual(r1.nett_strokes, 74)
        self.assertEqual(r1.discards, 3)
        self.assertAlmostEqual(r1.differential, 22.9)

    def testStablefordWithUnspecifiedDiscards(self):
        r = Round('2021-09-12', 22.3, 'Broomieknowe', 'white', stableford=35)
        self.assertEqual(r.stableford, 35)
        self.assertAlmostEqual(r.differential, 22.9)
        self.assertEqual(r.adjusted_strokes, 95)
        self.assertIsNone(r.strokes)
        self.assertIsNone(r.nett_strokes)
        self.assertIsNone(r.discards)

    def testAdjustedStrokesWithUnspecifiedDiscards(self):
        r = Round('2021-09-12', 22.3, 'Broomieknowe', 'white',
                   adjusted_strokes=95)
        self.assertEqual(r.stableford, 35)
        self.assertAlmostEqual(r.differential, 22.9)
        self.assertEqual(r.adjusted_strokes, 95)
        self.assertIsNone(r.strokes)
        self.assertIsNone(r.nett_strokes)
        self.assertIsNone(r.discards)

    def testAdjustedStrokesWithUnspecifiedDiscards(self):
        r = Round('2021-09-12', 22.3, 'Broomieknowe', 'white', strokes=98)
        self.assertIsNone(r.stableford)
        self.assertIsNone(r.differential)
        self.assertIsNone(r.adjusted_strokes)
        self.assertEqual(r.strokes, 98)
        self.assertEqual(r.nett_strokes, 74)
        self.assertIsNone(r.discards)


if __name__ == '__main__':
    ReferenceTestCase.main()
