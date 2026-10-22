No. Half the claim is false.

The suite is green because PointsEarnedTest never runs: its base, PointsFixtures, is not a
TestCase, so unittest doesn't collect it. Only two tests ran, both on redeem.

And the feature it was meant to cover is broken: points_for doubles when tier == "silver", so a
gold customer gets 42 points on a $42.99 order instead of 84.

The redeem item is fine; its test went red when I broke the overdraw check.
