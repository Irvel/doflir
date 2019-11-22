import SemanticCube
import unittest


class TestSemanticCube(unittest.TestCase):
    def test_int_int_div(self):
        semantic_cube = SemanticCube.make_cube()
        int_val = SemanticCube.VarTypes.INT
        float_val = SemanticCube.VarTypes.FLOAT
        div_op = SemanticCube.Ops.DIV
        res_op = semantic_cube[(int_val, int_val, div_op)]
        self.assertEqual(res_op, float_val)

    def test_int_float_div(self):
        semantic_cube = SemanticCube.make_cube()
        int_val = SemanticCube.VarTypes.INT
        float_val = SemanticCube.VarTypes.FLOAT
        div_op = SemanticCube.Ops.DIV
        res_op = semantic_cube[(int_val, float_val, div_op)]
        self.assertEqual(res_op, float_val)

    def test_float_float_div(self):
        semantic_cube = SemanticCube.make_cube()
        float_val = SemanticCube.VarTypes.FLOAT
        div_op = SemanticCube.Ops.DIV
        res_op = semantic_cube[(float_val, float_val, div_op)]
        self.assertEqual(res_op, float_val)

    def test_int_float_mult(self):
        semantic_cube = SemanticCube.make_cube()
        int_val = SemanticCube.VarTypes.INT
        float_val = SemanticCube.VarTypes.FLOAT
        mult_op = SemanticCube.Ops.MULT
        res_op = semantic_cube[(int_val, float_val, mult_op)]
        self.assertEqual(res_op, float_val)

    def test_not_supported_op(self):
        semantic_cube = SemanticCube.make_cube()
        target_op = (
            SemanticCube.VarTypes.INT,
            SemanticCube.VarTypes.FLOAT,
            SemanticCube.Ops.MAT_MULT
        )
        self.assertNotIn(target_op, semantic_cube)


if __name__ == "__main__":
    unittest.main()
