"""Regression for historical termination flags leaking into the next episode."""
import unittest
from types import SimpleNamespace as NS
import torch
import test_carrybox
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task

class FailureRewardTests(unittest.TestCase):
    def test_current_transition_gates_history_timeout_and_other_terminal(self):
        # Alive with past failure, new failure, timeout, unrelated terminal, both failure flags.
        flags={'fell':torch.tensor([True,True,True,False,True]),
               'tipped':torch.tensor([False,False,False,False,True])}
        manager=NS(terminated=torch.tensor([False,True,False,True,True]),
                   time_outs=torch.tensor([False,False,True,False,False]),get_term=flags.__getitem__)
        torch.testing.assert_close(task.failure_event(NS(termination_manager=manager)),
                                   torch.tensor([0.,1.,0.,0.,1.]))

    def test_reset_alive_sequence_has_only_one_penalty(self):
        flags={'fell':torch.tensor([False]),'tipped':torch.tensor([False])}
        manager=NS(terminated=torch.tensor([False]),time_outs=torch.tensor([False]),get_term=flags.__getitem__)
        env=NS(termination_manager=manager)
        results=[]
        for step in range(12):
            manager.terminated[:]=step==2
            if step==2:flags['tipped'][:]=True  # survives reset for statistics
            results.append(float(task.failure_event(env)))
        self.assertEqual(results,[0.,0.,1.]+[0.]*9)
        self.assertAlmostEqual(sum(results)*(-10.)*.02,-.2)

if __name__=='__main__':unittest.main()
